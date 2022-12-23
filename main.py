import sentry_sdk

import version
from conf import settings
from services.google_sheet_writer import GoogleSheetWriter
from services.mongodb_scraper import MongoDbScraper
from services.strapi_synchronizer import StrapiSynchronizer


def main():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        release=version.__version__,
        traces_sample_rate=1.0
    )
    print(f"Community synchronizer {version.__version__}")
    print("------------------------")

    # 1. Get list of communities from specific sheet column
    google_sheet_writer = GoogleSheetWriter()
    communities = google_sheet_writer.get_communities()

    # 2. Scrape MongoDB according to the list of communities, returns only list of successfully scraped communities
    all_communities, scraped_communities = MongoDbScraper.create_from_communities(
        communities=communities
    ).scrape_mongodb()

    # 3. Synchronize Strapi communities according to scraped data
    StrapiSynchronizer.create_from_communities(
        communities=communities
    ).sync_strapi(scraped_communities=scraped_communities)

    # 4. Write data into specific Google sheet
    google_sheet_writer.write_data(all_data=all_communities)


if __name__ == '__main__':
    main()


def lambda_handler(event, context):
    main()
