# Strapi synchronizer 📝

Script for scraping specific content from Mongo database to write results to Google sheet and synchronise them to the Strapi CMS.

## Dependencies

[pymongo](https://pymongo.readthedocs.io/en/stable/) for communication with Mongo database.

[pygsheets](https://pygsheets.readthedocs.io/en/stable/) for communication with Google Worksheet API.

[pydantic](https://pydantic-docs.helpmanual.io/) for settings variables.

[python-dotenv](https://saurabh-kumar.com/python-dotenv/) for sensitive data stored in environment variables.

## Basic setup
- To install dependencies, it's recommended to create `venv` environment, install [Poetry - Dependency and Management tool](https://python-poetry.org/) and run command: `poetry install`.

- Set up environment variables in the `.env` file according to `.env.example` file.

- Set up settings variables in the `conf.py` file.

- Command to run the script: `python main.py`.

---
Made with 💜 by CulturePulse s.r.o. (c) 2022
