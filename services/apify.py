"""
Cliente de la Apify API para leer items de un dataset.
Se usa después de recibir el webhook ACTOR.RUN.SUCCEEDED.
"""
import httpx
from app.config import settings


APIFY_API_BASE = "https://api.apify.com/v2"


def fetch_dataset_items(dataset_id: str) -> list[dict]:
    """
    Descarga todos los items de un dataset de Apify.

    Args:
        dataset_id: ID del dataset (viene en resource.defaultDatasetId del webhook payload).

    Returns:
        Lista de dicts con los posts scrapeados.

    Raises:
        httpx.HTTPStatusError: si la API responde con error.
    """
    url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"
    params = {
        "token": settings.apify_token,
        "format": "json",
        "clean": "true",   # omite items vacíos
        "limit": 200,      # máximo razonable por run
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()
