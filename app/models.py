from pydantic import BaseModel, field_validator
from typing import Optional, Literal

class ApifyPost(BaseModel):
    url: str
    ownerUsername: Optional[str] = None
    caption: Optional[str] = None
    timestamp: Optional[str] = None
    videoTranscript: Optional[str] = None

    @field_validator("url")
    def url_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        return v

class AgentResponse(BaseModel):
    status: Literal["saved", "skipped", "error"]
    title: Optional[str] = None
    doc: Optional[str] = None
    reason: Optional[str] = None
