# Community synchronizer 📝

Script for scraping communities and their data from Mongo database to write their results into the Google sheet and to synchronise them with the Strapi CMS.

## Dependencies

[pymongo](https://pymongo.readthedocs.io/en/stable/) for a communication with the Mongo database.

[pygsheets](https://pygsheets.readthedocs.io/en/stable/) for a communication with the Google Worksheet API.

[pydantic](https://pydantic-docs.helpmanual.io/) for the settings variables.

[python-dotenv](https://saurabh-kumar.com/python-dotenv/) for sensitive data stored in the environment variables.

## Basic setup
- To install dependencies, it's recommended to create `venv` (virtual environment), there install 
[Poetry - Dependency and Management tool](https://python-poetry.org/) and run command: `poetry install`.


- Set up environment variables in the `.env` file according to `.env.example` file.


- Set up settings variables in the `conf.py` file.


- For successful connection into the Google sheets, you need to provide an OAuth credentials as a `credentials.json` file in the project root directory. Go to\
[Google Console - Credentials](https://console.cloud.google.com/projectselector2/apis/credentials?supportedpurview=project), 
select your project, create Service Account and Key and download the JSON file. More Information in pygsheets
[docs](https://pygsheets.readthedocs.io/en/stable/authorization.html#service-account).


- Command to run the script: `python main.py`.

## Deployment
Deployment is managed by [AWS Serverless Application Model (SAM)](https://aws.amazon.com/serverless/sam/).

Now, deployment is fully automatic due to the GitHub CI/CD service. So all you need to do is to test the project and push
feature/fix/change branch to the Git repository. Create a merge request and after a code-review process, this feature will be merged and deployed automatically.

If you still, for some reason need to deploy this project to the AWS Lambda manually, or want to know, how it works, section below is written for you. 

### AWS cli / SAM cli
To manage the deployment process, aws cli and sam cli is required. For this tool iam use is needed with setup
access and secret key. User needs following permissions:

| AWS Service                |  Permission   |
|----------------------------|:-------------:|
| AWSCloudFormation          |  FullAccess   |
| IAM                        |  FullAccess   |
| AWSLambda                  |  FullAccess   |
| AmazonAPIGateway           | Administrator |
| AmazonS3                   |  FullAccess   |
| AmazonEC2ContainerRegistry |  FullAccess   |

- To install SAM cli, just install: `pip install aws-sam-cli`.
- To install AWS cli, just install: `pip install awscli`.

> NOTE: For build of the project is needed file `credentials.json` which is not downloaded from the repository. More information\
> in the [**Basic setup**](#Basic setup).

> NOTE: `template.yaml` as SAM configuration file is also needed (for now it stores secrets), so It needs to be provided\
> by developer manually (ask me: **adam@culturepulse.ai**).

### AWS SAM template
File `template.yaml` stores settings for the lambda function deployment. The most important part are `Layers`. \
This attribute stores all necessary dependencies, which needs to be installed as a "Layer". Luckily we have open-source \
GitHub repository with already installed layers here: [Klayers](https://github.com/keithrozario/Klayers).

### Generate requirements.txt from poetry
To generate requirements.txt file, you need to run following command: `poetry export --without-hashes --format=requirements.txt > requirements.txt`

### Build project
If you have an existing `.aws-sam` directory in your project root, delete it.\
To build the project, you need command: `sam build --use-container`.

### Test the built project locally

To run and test the project locally before the deployment, run command: `sam local invoke`.

### Deploy

To deploy the project, run command: `sam deploy`.

## Contribution TODO
- Add AWS Secrets Manager support (for now all secrets inside GitHub Secrets - dirty solution).
- Change to private GitHub repository (for now due to free GitHub actions policy).

---
Made with 💜 by CulturePulse s.r.o. (c) 2022
