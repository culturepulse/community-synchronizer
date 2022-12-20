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
    blacklist_premium_communities = [
        'cars'
    ]
    strapi_api_client = StrapiApiClient(
        api_url=settings.STRAPI_URL,
        token=f"Bearer {settings.STRAPI_API_KEY}"
    )

    for index, community in enumerate(communities, 1):
        print(f'{index}/{len(communities)} - Syncing {community}.')

        # Community not in Strapi
        community_response = strapi_api_client.get_community(name=community)
        data = community_response.get('data')

        if not data or len(data) <= 0:
            # But if community is already scraped, add to Strapi
            if community in scraped_communities:
                # All communities by default should be premium except blacklist ones
                if community in blacklist_premium_communities:
                    is_premium = False
                else:
                    is_premium = True

                strapi_api_client.create_community(data={'name': community, 'isPremium': is_premium})

        # Community in Strapi
        else:
            # But if community is not scraped, delete from Strapi
            if community not in scraped_communities:
                strapi_api_client.delete_community(community_id=data[0]['id'])


def add_sheet_row(row_data: dict, all_data: dict) -> dict:
    all_data['Interest Group'].append(row_data['Interest Group'])
    all_data['Community'].append(row_data['Community'])
    all_data['Reason'].append(row_data['Reason'])
    all_data['Status'].append(row_data['Status'])
    all_data['Documents'].append(row_data['Documents'])
    all_data['Strapi'].append(row_data['Strapi'])
    all_data['Date'].append(row_data['Date'])
    all_data['topicModelAnalysis'].append(row_data['topicModelAnalysis'])
    all_data['marketprofile'].append(row_data['marketprofile'])
    all_data['psychData'].append(row_data['psychData'])
    return all_data


def scrape_mongodb(communities: list) -> Tuple[dict, list]:
    # Connect to MongoDB database
    mongodb_service = MongoDbService.create_from_connection(connection=settings.MONGODB_CONNECTION)

    # Get needed databases
    campaign_data_db = mongodb_service.get_database(name='campaign_data')
    culturepulse_social_media_db = mongodb_service.get_database(name='culturepulse_social_media')

    # Get needed collections
    campaign_results_collection = mongodb_service.get_collection(database=campaign_data_db, name='campaign_results')

    all_data = {
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

        # If result for specific community name in the MongoDB
        if result:
            social_media_collection = mongodb_service.get_collection(
                database=culturepulse_social_media_db, name=f'reddit_data_{community}'
            )
            document_count = (social_media_collection.estimated_document_count() or 0)

            # TODO: create dataclass
            row_data = {
                'Interest Group': result.get('interest_group', ''),
                'Community': result['community'],
                'Reason': '',
                'Status': 'Finished',
                'Documents': document_count,
                'Strapi': True,
                'Date': result['timestamp'],
                'topicModelAnalysis': True,
                'marketprofile': True,
                'psychData': True
            }

            # 1. If scraped less than 200 documents
            if document_count < 200:
                row_data['Status'] = 'Not scraped'
                row_data['Strapi'] = False
                row_data['Reason'] = 'Documents < 200'
                row_data['topicModelAnalysis'] = False
                row_data['marketprofile'] = False
                row_data['psychData'] = False
                all_data = add_sheet_row(row_data=row_data, all_data=all_data)
                continue

            # 2. If not REDDIT data in result
            reddit_result = result.get('reddit')
            if not reddit_result:
                row_data['Status'] = 'Not analysed'
                row_data['Strapi'] = False
                row_data['Reason'] = 'Not found "reddit object"'
                row_data['topicModelAnalysis'] = False
                row_data['marketprofile'] = False
                row_data['psychData'] = False
                all_data = add_sheet_row(row_data=row_data, all_data=all_data)
                continue

            # 3. If not "topicModelAnalysis" or "marketprofile" or "psychData"
            topic_model_analysis = reddit_result.get('topicModelAnalysis')
            market_profile = reddit_result.get('marketprofile')
            psych_data = reddit_result.get('psychData')

            if not topic_model_analysis or not market_profile or not psych_data:
                reasons = []
                statuses = []
                row_data['Strapi'] = False

                # If not "topicModelAnalysis"
                if not topic_model_analysis:
                    reasons.append('topicModelAnalysis')
                    statuses.append('Not analysed')
                    row_data['topicModelAnalysis'] = False

                # If not "psychData" or "marketprofile"
                if not psych_data or not market_profile:
                    statuses.append('Not profiled')

                    if not psych_data:
                        reasons.append('psychData')
                        row_data['psychData'] = False
                    if not market_profile:
                        reasons.append('marketprofile')
                        row_data['marketprofile'] = False

                row_data['Reason'] = f'Not found: {",".join(reasons)}'
                row_data['Status'] = ','.join(statuses)
                all_data = add_sheet_row(row_data=row_data, all_data=all_data)
                continue

            # 4. If all good, add community name to "scraped_communities" list
            all_data = add_sheet_row(row_data=row_data, all_data=all_data)
            scraped_communities.append(community)

        # If NO result for specific community name in the MongoDB
        else:
            all_data['Status'].append('Not scraped')
            all_data['Reason'].append('Not found in "campaign_results"')
            all_data['Interest Group'].append('')
            all_data['Community'].append(community)
            all_data['Date'].append('')
            all_data['Documents'].append(0)
            all_data['Strapi'].append(False)
            all_data['topicModelAnalysis'].append(False)
            all_data['marketprofile'].append(False)
            all_data['psychData'].append(False)

    return all_data, scraped_communities


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
