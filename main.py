from datetime import datetime
from typing import Tuple

import pandas
import pygsheets
# import sentry_sdk
from pygsheets import Cell
from services.google_sheet import GoogleSheetService
from services.mongodb import MongoDbService
from conf import settings
from services.strapi.api_client import StrapiApiClient


def get_communities(spreadsheet) -> list:
    sheet = spreadsheet[1]
    communities = list(dict.fromkeys(sheet.get_col(col=1, include_tailing_empty=False)[1:]))

    return communities


def sync_strapi(communities: list, scraped_communities: list):
    strapi_api_client = StrapiApiClient(
        api_url=settings.STRAPI_URL,
        token=f"Bearer {settings.STRAPI_API_KEY}"
    )

    for index, community in enumerate(communities, 1):
        print(f'{index}/{len(communities)} - Syncing {community}.')

        # Community not in Strapi
        community_response = strapi_api_client.get_community(name=community)
        data = community_response.get('data')

        if data:
            if len(data) <= 0:
                # But if community is already scraped, add to Strapi
                if community in scraped_communities:
                    strapi_api_client.create_community(data={'name': community, 'isPremium': False})
            # Community in Strapi
            else:
                # But if community is not scraped, delete from Strapi
                if community not in scraped_communities:
                    strapi_api_client.delete_community(community_id=data[0]['id'])
        else:
            print(f'No data: {community_response}')


def scrape_mongodb(communities: list) -> Tuple[dict, list]:
    # Connect to MongoDB database
    mongodb_service = MongoDbService.create_from_connection(connection=settings.MONGODB_CONNECTION)

    # Get needed databases
    campaign_data_db = mongodb_service.get_database(name='campaign_data')
    culturepulse_social_media_db = mongodb_service.get_database(name='culturepulse_social_media')

    # Get needed collections
    campaign_results_collection = mongodb_service.get_collection(database=campaign_data_db, name='campaign_results')

    data = {
        'Interest Group': [],
        'Community': [],
        'Reason': [],
        'Status': [],
        'Documents': [],
        'Strapi': [],
        'Date': [],
        'topicModelAnalysis': [],
        'marketprofile': [],
        'psychData': []
    }
    scraped_communities = []

    # Scrape data to "data" variable
    for index, community in enumerate(communities, 1):
        print(f'{index}/{len(communities)} - Scraping {community}.')
        result = campaign_results_collection.find_one(
            {"community": {'$exists': True}, "source": "reddit", "community": community}
        )

        if result:
            data['Interest Group'].append(result.get('interest_group', ''))
            data['Community'].append(result['community'])
            data['Date'].append(result['timestamp'])

            social_media_collection = mongodb_service.get_collection(
                database=culturepulse_social_media_db, name=f'reddit_data_{community}'
            )
            count = (social_media_collection.estimated_document_count() or 0)

            data['Documents'].append(count)

            reddit_result = result.get('reddit')
            if not reddit_result:
                data['Status'].append('Not scraped')
                data['Strapi'].append(False)
                data['Reason'].append('Not found "reddit object"')
                data['topicModelAnalysis'].append(False)
                data['marketprofile'].append(False)
                data['psychData'].append(False)
            else:
                topic_model_analysis = reddit_result.get('topicModelAnalysis')
                market_profile = reddit_result.get('marketprofile')
                psych_data = reddit_result.get('psychData')

                # If all analyzed data are valid
                if topic_model_analysis and market_profile and psych_data:
                    # All scraped and fully functional communities
                    data['topicModelAnalysis'].append(True)
                    data['marketprofile'].append(True)
                    data['psychData'].append(True)

                    if count >= 200:
                        scraped_communities.append(community)
                        data['Status'].append('Scraped')
                        data['Strapi'].append(True)
                        data['Reason'].append('')
                    else:
                        data['Status'].append('In progress')
                        data['Strapi'].append(False)
                        data['Reason'].append('Documents < 200')
                # If some of needed data are not valid
                else:
                    reasons = []
                    data['Status'].append('Not scraped')
                    data['Strapi'].append(False)

                    if not reddit_result.get('topicModelAnalysis'):
                        reasons.append('topicModelAnalysis')
                        data['topicModelAnalysis'].append(False)
                    else:
                        data['topicModelAnalysis'].append(True)

                    if not reddit_result.get('marketprofile'):
                        reasons.append('marketprofile')
                        data['marketprofile'].append(False)
                    else:
                        data['marketprofile'].append(True)

                    if not reddit_result.get('psychData'):
                        reasons.append('psychData')
                        data['psychData'].append(False)
                    else:
                        data['psychData'].append(True)
                    data['Reason'].append(f'Not found: {str(reasons)}')
        else:
            data['Status'].append('Not scraped')
            data['Reason'].append('Not found in "campaign_results"')
            data['Interest Group'].append('')
            data['Community'].append(community)
            data['Date'].append('')
            data['Documents'].append(0)
            data['Strapi'].append(False)
            data['topicModelAnalysis'].append(False)
            data['marketprofile'].append(False)
            data['psychData'].append(False)

    return data, scraped_communities


def write_data(spreadsheet, data: dict):
    data_frame = pandas.DataFrame(data)
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet = spreadsheet[0]
    sheet.clear()

    # Order values and normalize NaN values
    data_frame = data_frame.sort_values(by=['Interest Group', 'Community'], ascending=[False, True]).fillna('')
    sheet.set_dataframe(data_frame, start='A1')
    sheet.update_value('K1', "Scraped at:")
    sheet.update_value('L1', time_now)

    model_cell = Cell('A1')
    model_cell.set_text_format('bold', True)
    model_cell.set_text_format('fontSize', 12)

    title_range = pygsheets.DataRange(start='A1', end='J1', worksheet=sheet)
    title_range.apply_format(model_cell)


def main():
    # TODO: Add Sentry integration (AWS Lambda size issue)
    # sentry_sdk.init(
    #     dsn=settings.SENTRY_DSN,
    #     release=version.__version__,
    #     traces_sample_rate=1.0
    # )
    # print(f"Strapi synchronizer {version.__version__}")
    # print("------------------------")

    # 1. Get Spreadsheet
    google_sheet_service = GoogleSheetService.create_from_scope(scope=settings.GOOGLE_SCOPE)
    spreadsheet = google_sheet_service.get_sheet(settings.GOOGLE_SPREADSHEET_ID)

    # 2. Get list of communities from specific sheet column
    communities = get_communities(spreadsheet)

    # 3. Scrape MongoDB according to the list of communities, returns only list of successfully scraped communities
    data, scraped_communities = scrape_mongodb(communities=communities)

    # 4. Synchronize Strapi communities according to scraped data
    sync_strapi(communities=communities, scraped_communities=scraped_communities)

    # 5. Write data into specific Google sheet
    write_data(spreadsheet=spreadsheet, data=data)


if __name__ == '__main__':
    main()


def lambda_handler(event, context):
    main()
