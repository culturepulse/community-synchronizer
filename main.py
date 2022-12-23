import dataclasses
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Tuple, List, Union
from zoneinfo import ZoneInfo

import pandas
import pygsheets
# import sentry_sdk
from pygsheets import Cell
from services.google_sheet import GoogleSheetService
from services.mongodb import MongoDbService
from conf import settings
from services.strapi.api_client import StrapiApiClient


@dataclass
class CommunityTitleRow:
    interest_group: str
    community: str
    documents: str
    date: str
    reason: str
    status: str
    strapi: str
    topic_model_analysis: str
    market_profile: str
    psych_data: str


@dataclass
class CommunityContentRow:
    interest_group: str
    community: str
    documents: int
    date: str
    reason: str = ''
    status: str = 'Finished'
    strapi: bool = True
    topic_model_analysis: bool = True
    market_profile: bool = True
    psych_data: bool = True


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


def scrape_mongodb(communities: list) -> Tuple[List[Union[CommunityTitleRow, CommunityContentRow]], List[str]]:
    # Connect to MongoDB database
    mongodb_service = MongoDbService.create_from_connection(connection=settings.MONGODB_CONNECTION)

    # Get needed databases
    campaign_data_db = mongodb_service.get_database(name='campaign_data')
    culturepulse_social_media_db = mongodb_service.get_database(name='culturepulse_social_media')

    # Get needed collections
    campaign_results_collection = mongodb_service.get_collection(database=campaign_data_db, name='campaign_results')
    scraped_communities = []
    all_rows = []

    # Scrape data to "data" variable
    all_rows.append(CommunityTitleRow(
        interest_group='Interest Group',
        community='Community',
        reason='Reason',
        status='Status',
        documents='Documents',
        strapi='Strapi',
        date='Date',
        topic_model_analysis='topicModelAnalysis',
        market_profile='marketprofile',
        psych_data='psychData'
    ))

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
            row_data = CommunityContentRow(
                community=result.get('community', ''),
                interest_group=result.get('interest_group', ''),
                documents=document_count,
                date=result['timestamp'].astimezone(tz=ZoneInfo('Europe/Bratislava')).strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(result['timestamp'], datetime) else str(result['timestamp'])
            )

            # 1. If scraped less than 200 documents
            if document_count < 200:
                row_data.status = 'Not scraped'
                row_data.strapi = False
                row_data.reason = 'Documents < 200'
                row_data.topic_model_analysis = False
                row_data.market_profile = False
                row_data.psych_data = False

                all_rows.append(row_data)
                continue

            # 2. If not REDDIT data in result
            reddit_result = result.get('reddit')
            if not reddit_result:
                row_data.status = 'Not analysed'
                row_data.strapi = False
                row_data.reason = 'Not found "reddit object"'
                row_data.topic_model_analysis = False
                row_data.market_profile = False
                row_data.psych_data = False

                all_rows.append(row_data)
                continue

            # 3. If not "topicModelAnalysis" or "marketprofile" or "psychData"
            topic_model_analysis = reddit_result.get('topicModelAnalysis')
            market_profile = reddit_result.get('marketprofile')
            psych_data = reddit_result.get('psychData')

            if not topic_model_analysis or not market_profile or not psych_data:
                reasons = []
                statuses = []
                row_data.strapi = False

                # If not "topicModelAnalysis"
                if not topic_model_analysis:
                    reasons.append('topicModelAnalysis')
                    statuses.append('Not analysed')
                    row_data.topic_model_analysis = False

                # If not "psychData" or "marketprofile"
                if not psych_data or not market_profile:
                    statuses.append('Not profiled')

                    if not psych_data:
                        reasons.append('psychData')
                        row_data.psych_data = False
                    if not market_profile:
                        reasons.append('marketprofile')
                        row_data.market_profile = False

                row_data.reason = f'Not found: {",".join(reasons)}'
                row_data.status = ','.join(statuses)

                all_rows.append(row_data)
                continue

            # 4. If all good, add community name to "scraped_communities" list
            all_rows.append(row_data)
            scraped_communities.append(community)

        # If NO result for specific community name in the MongoDB
        else:
            row_data = CommunityContentRow(
                interest_group='',
                community=community,
                reason='Not found in "campaign_results"',
                status='Not scraped',
                documents=0,
                strapi=False,
                date='',
                topic_model_analysis=False,
                market_profile=False,
                psych_data=False
            )
            all_rows.append(row_data)

    return all_rows, scraped_communities


def write_data(spreadsheet, all_data: List[Union[CommunityTitleRow, CommunityContentRow]]):
    time_now = datetime.now(tz=ZoneInfo('Europe/Bratislava')).strftime("%Y-%m-%d %H:%M:%S")
    sheet = spreadsheet[0]
    sheet.clear()

    # Order values and normalize NaN values
    # data_frame = data_frame.sort_values(by=['Interest Group', 'Community'], ascending=[False, True]).fillna('')
    cells_to_insert = []
    for row_index, item in enumerate(all_data, 1):
        [getattr(item, field.name) for field in dataclasses.fields(item)]
        for col_index, field in enumerate(dataclasses.fields(item), 1):
            cells_to_insert.append(Cell(pos=f'{chr(col_index+64)}{row_index}', val=getattr(item, field.name)))

    sheet.update_cells(cells_to_insert)

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
    all_communities, scraped_communities = scrape_mongodb(communities=communities)

    # 4. Synchronize Strapi communities according to scraped data
    # sync_strapi(communities=communities, scraped_communities=scraped_communities)

    # 5. Write data into specific Google sheet
    write_data(spreadsheet=spreadsheet, all_data=all_communities)


if __name__ == '__main__':
    main()


def lambda_handler(event, context):
    main()
