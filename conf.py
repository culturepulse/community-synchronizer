from pydantic import BaseSettings


class Settings(BaseSettings):
    MONGODB_CONNECTION_STRING: str
    STRAPI_API_KEY: str
    GOOGLE_SCOPE: str = "https://www.googleapis.com/auth/spreadsheets"
    GOOGLE_SPREADSHEET_ID: str = None
    GOOGLE_SPREADSHEET_NAME: str = "Analyzed MongoDB communities"

    class Config:
        env_file = ".env"


settings = Settings()
