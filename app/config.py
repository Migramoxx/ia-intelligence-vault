import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    google_service_account_json: str
    google_drive_folder_id: str
    webhook_secret: str

    class Config:
        env_file = ".env"

try:
    settings = Settings()
except Exception as e:
    raise ValueError(f"Faltan variables de entorno requeridas o son invalidas: {e}")
