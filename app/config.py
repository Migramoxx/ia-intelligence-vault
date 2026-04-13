import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    google_service_account_json: str
    google_drive_folder_id: str
    webhook_secret: str
    apify_token: str

    # Perfiles de Instagram a monitorear (separados por coma)
    instagram_profiles: str = (
        "agustinbadt,fabriguaglianone,miguelbaenaia,mr.pink,soyenriquerocha"
    )

    model_config = {"env_file": ".env"}


try:
    settings = Settings()
except Exception as e:
    raise ValueError(f"Faltan variables de entorno requeridas: {e}")
