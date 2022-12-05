from datetime import datetime

import pandas
import pygsheets
from pygsheets import Cell

from services.google_sheet import GoogleSheetService
from services.mongodb import MongoDbService
from conf import settings
from communities import communities
from services.strapi_api_client import StrapiApiClient


def main():
    # Connect to MongoDB database
    mongodb_service = MongoDbService.create_from_connection(connection=settings.MONGODB_CONNECTION_STRING)

    # Get needed databases
    campaign_data_db = mongodb_service.get_database(name='campaign_data')
    culturepulse_social_media_db = mongodb_service.get_database(name='culturepulse_social_media')

    # Get needed collections
    campaign_results_collection = mongodb_service.get_collection(database=campaign_data_db, name='campaign_results')

    # Print campaign results data
    data = {
        'Interest Group': [], 'Community': [], 'Reason': [], 'Status': [], 'Documents': [], 'Strapi': [], 'Date': []
    }
    scraped_communities = []
    strapi_api_client = StrapiApiClient()

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

            if not result['reddit'].get('topicModelAnalysis'):
                data['Status'].append('Not scraped')
                data['Strapi'].append(False)
                data['Reason'].append('Not found "topicModelAnalysis"')
            else:
                # All scraped and fully functional communities
                if count >= 200:
                    scraped_communities.append(community)
                    data['Status'].append('Scraped')
                    data['Strapi'].append(True)
                    data['Reason'].append('')
                else:
                    data['Status'].append('In progress')
                    data['Strapi'].append(False)
                    data['Reason'].append('Documents < 200')
        else:
            data['Status'].append('Not scraped')
            data['Reason'].append('Not found in "campaign_results"')
            data['Interest Group'].append('')
            data['Community'].append(community)
            data['Date'].append('')
            data['Documents'].append(0)
            data['Strapi'].append(False)

    # Sync Strapi
    for index, community in enumerate(communities, 1):
        print(f'{index}/{len(communities)} - Syncing {community}.')

        # Community not in Strapi
        community_response = strapi_api_client.get_community(name=community)['data']
        if len(community_response) <= 0:
            # But if community is already scraped, add to Strapi
            if community in scraped_communities:
                strapi_api_client.create_community(data={'name': community, 'isPremium': False})
        # Community in Strapi
        else:
            # But if community is not scraped, delete from Strapi
            if community not in scraped_communities:
                strapi_api_client.delete_community(community_id=community_response[0]['id'])

    data_frame = pandas.DataFrame(data)
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    google_sheet_service = GoogleSheetService.create_from_scope(scope=settings.GOOGLE_SCOPE)
    sheet = google_sheet_service.get_sheet(settings.GOOGLE_SPREADSHEET_ID)
    worksheet = sheet[0]
    worksheet.clear()

    data_frame = data_frame.sort_values(by=['Status', 'Community'], ascending=[False, True])
    worksheet.set_dataframe(data_frame, start='A1')
    worksheet.update_value('H1', "Scraped at:")
    worksheet.update_value('I1', time_now)

    model_cell = Cell('A1')
    model_cell.set_text_format('bold', True)
    model_cell.set_text_format('fontSize', 12)

    title_range = pygsheets.DataRange(start='A1', end='G1', worksheet=worksheet)
    title_range.apply_format(model_cell)


if __name__ == '__main__':
    main()


def lambda_handler(event, context):
    main()
