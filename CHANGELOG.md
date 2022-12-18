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
