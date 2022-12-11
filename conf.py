from pydantic import BaseSettings


class Settings(BaseSettings):
    MONGODB_CONNECTION: str
    STRAPI_URL: str
    STRAPI_API_KEY: str
    GOOGLE_SCOPE: str = "https://www.googleapis.com/auth/spreadsheets"
    GOOGLE_SPREADSHEET_ID: str = None
    SENTRY_DSN: str

    class Config:
        env_file = ".env"


settings = Settings()
