## 0.1.0 : 11.12.2022

- **Added**: Integration with the `MongoDB`
- **Added**: Integration with the `Google Sheets` API
- **Added**: Integration with the `Strapi` API
- **Added**: Integration with the `Sentry` monitoring tool
- **Added**: GitHub Actions CI/CD workflow
- **Added**: AWS automatic deployment as scheduled CRON job through AWS Lambda

## 0.1.1 : 12.12.2022

- **Changed**: Ordering of Interest groups column in the sheet
- **Fixed**: Replacing NaN values with empty string to normalise data

## 0.1.2 : 18.12.2022

- **Added**: Three new columns into the sheet `topicModelAnalysis`, `marketprofile` and `psychData`
- **Added**: New `Scraped` status checkers according to these new added columns
- **Added**: Sentry support (for now inactive due to AWS Lambda limitations)
- **Changed**: Updated `Reason` column message format

## 0.1.3 : 20.12.2022

- **Added**: Changed error handling to be conditional, more readable and intuitive
- **Added**: Add new statuses: `Not analysed`, `Not profiled`
- **Changed**: Renamed `Scraped` status to `Finished`
- **Fix**: Communication with strapi is now established correctly

## 0.2.0 : 23.12.2022

- **Removed**: Pandas dependency
- **Added**: Sentry integration

## 0.2.1 : 03.01.2023

- **Changed**: Deployment is made after release, not a main branch push operation
- **Changed**: Get sheet operation is made by name, not by an index
- **Changed**: Some minor README.md notes has been rewritten

## 0.2.2 : 04.01.2023

- **Changed**: Add the newest strapi-api-client dependency support (0.3.0)

## 0.2.3 : 27.03.2023

- **Fix**: Raised timeout lambda connection from 120s to 600s


## 0.2.4 : 18.07.2023

- **Fix**: Renamed data object to "data".
