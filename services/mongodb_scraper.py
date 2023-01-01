import math
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, List, Union
from zoneinfo import ZoneInfo

from conf import settings
from services.mongodb_client import MongoDbClient


class MongoDbScraper:
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

    def __init__(self, communities: List[str]):
        self._communities = communities

    @classmethod
    def create_from_communities(cls, communities: List[str]) -> 'MongoDbScraper':
        return MongoDbScraper(communities=communities)

    def scrape_mongodb(self) -> Tuple[List[Union[CommunityTitleRow, CommunityContentRow]], List[str]]:
        # Connect to MongoDB database
        mongodb_service = MongoDbClient.create_from_connection(connection=settings.MONGODB_CONNECTION)

        # Get needed databases
        campaign_data_db = mongodb_service.get_database(name='campaign_data')
        culturepulse_social_media_db = mongodb_service.get_database(name='culturepulse_social_media')

        # Get needed collections
        campaign_results_collection = mongodb_service.get_collection(database=campaign_data_db, name='campaign_results')
        scraped_communities = []
        all_rows = [self.CommunityTitleRow(
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
        )]

        # Scrape data to "data" variable

        for index, community in enumerate(self._communities, 1):
            print(f'{index}/{len(self._communities)} - Scraping {community}.')
            result = campaign_results_collection.find_one(
                {"community": {'$exists': True}, "source": "reddit", "community": community}
            )

            # If result for specific community name in the MongoDB
            if result:
                social_media_collection = mongodb_service.get_collection(
                    database=culturepulse_social_media_db, name=f'reddit_data_{community}'
                )
                document_count = (social_media_collection.estimated_document_count() or 0)
                interest_group = result.get('interest_group', '')
                if isinstance(interest_group, float):
                    if math.isnan(interest_group):
                        interest_group = ''

                row_data = self.CommunityContentRow(
                    community=result.get('community', ''),
                    interest_group=interest_group,
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
                row_data = self.CommunityContentRow(
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
