from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    PROJECT_ID: str = "meter-to-cash-sim"
    GCP_REGION: str = "us-central1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://meter_user:meter_pass@localhost:5432/meter_to_cash"
    
    # Auth
    API_KEY_SECRET: str = "dev-secret-key"
    
    # GCP Configurations
    GCS_BUCKET_RAW: str = "meter-raw-dev"
    BQ_DATASET_STAGING: str = "meter_to_cash_staging"
    BQ_DATASET_CORE: str = "meter_to_cash_core"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
