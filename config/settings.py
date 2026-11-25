"""PolishMeter project application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PolishMeter"
    subpage_about_name: str = "PolishMeter - About"
    subpage_contact_name: str = "PolishMeter - Contact"
    timeout: int = 20
    gus_bdl_api_url: str = "https://bdl.stat.gov.pl/api/v1/"
    web_page: str = "http://127.0.0.1:8000"
    subpage_about: str = "/about"
    subpage_contact: str = "/contact"
    gus_bdl_indicators_file: str = "gus_bdl_indicators.json"
    database_path: str = "data/data.db"

settings = Settings()
