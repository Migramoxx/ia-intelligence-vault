from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal


class ApifyPost(BaseModel):
    """
    Modelo de un post de Instagram scrapeado por apify/instagram-scraper.
    Los campos vienen del dataset output estándar del actor.
    """
    url: str
    ownerUsername: Optional[str] = None
    caption: Optional[str] = None
    timestamp: Optional[str] = None
    videoTranscript: Optional[str] = None  # Solo presente si viene del Transcript Extractor

    @field_validator("url")
    def url_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        return v

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: dict) -> dict:
        """
        Normaliza campos de distintos actores de Apify al schema unificado.
        - apify/instagram-scraper: ya tiene url, caption, ownerUsername, timestamp
        - bulletproof/instagram-transcript-extractor: tiene transcript.full_text y metadata.title
        """
        # Soporte para Transcript Extractor
        if "transcript" in data and isinstance(data["transcript"], dict):
            data.setdefault("videoTranscript", data["transcript"].get("full_text"))
        if "metadata" in data and isinstance(data["metadata"], dict):
            data.setdefault("caption", data["metadata"].get("title") or data["metadata"].get("description"))

        # Construir URL desde shortCode si no viene url directa
        if not data.get("url") and data.get("shortCode"):
            data["url"] = f"https://www.instagram.com/p/{data['shortCode']}/"

        return data


class ApifyResource(BaseModel):
    """Parte del payload del webhook de Apify que identifica el dataset."""
    defaultDatasetId: str


class ApifyWebhookPayload(BaseModel):
    """
    Payload que Apify envía al webhook cuando un Actor.run.SUCCEEDED.
    Estructura: https://docs.apify.com/platform/integrations/webhooks/events
    """
    resource: ApifyResource


class AgentResponse(BaseModel):
    status: Literal["saved", "skipped", "error"]
    title: Optional[str] = None
    doc: Optional[str] = None
    reason: Optional[str] = None


class BatchResponse(BaseModel):
    """Respuesta del webhook cuando procesa múltiples posts de un perfil."""
    status: str = "ok"
    total: int = 0
    saved: int = 0
    skipped: int = 0
    errors: int = 0
