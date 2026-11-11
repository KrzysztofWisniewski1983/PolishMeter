"""PolishMeter project application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "PolishMeter"
    timeout: int = 20
    gus_bdl_api_url: str = "https://bdl.stat.gov.pl/api/v1/"
    web_page: str = "http://127.0.0.1:8000"
    subpage_about: str = "/about"
    subpage_contact: str = "/contact"

settings = Settings()
