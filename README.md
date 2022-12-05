# MongoDB Scraper 📝

Script for scraping specific content from Mongo database to write results to google sheet.

## Dependencies

[pymongo](https://pymongo.readthedocs.io/en/stable/) for communication with Mongo database.

[pygsheets](https://pygsheets.readthedocs.io/en/stable/) for communication with Google Worksheet API.

[pydantic](https://pydantic-docs.helpmanual.io/) for settings variables.

[python-dotenv](https://saurabh-kumar.com/python-dotenv/) for sensitive data stored in environment variables.

## Basic setup
- To install dependencies, it's recommended to create `venv` environment, install [Poetry - Dependency and Management tool](https://python-poetry.org/) and run command: `poetry install`.


- Add `credentials.json` (file containing **OAuth 2.0 Client ID**) into the project root. 
This file can be downloaded from your **Google Cloud Console**.


- Set up environment variables in the `.env` file according to `.env.example` file.


- Command to run the script: `python main.py`

---
Made with 💜 by CulturePulse s.r.o. (c) 2022
