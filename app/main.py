from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from contextlib import asynccontextmanager

from app.config import settings
from app.models import ApifyPost, AgentResponse
from services import gdocs, dedup
from app import agent

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.webhook_secret:
        return api_key_header
    raise HTTPException(status_code=401, detail="Invalid API Key")

@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = settings.anthropic_api_key
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/webhook", response_model=AgentResponse)
async def webhook(post: ApifyPost, api_key: str = Depends(get_api_key)):
    if not post.caption and not post.videoTranscript:
        return AgentResponse(status="error", reason="invalid_input")

    try:
        doc_id = gdocs.get_or_create_doc("IA_Intelligence_Vault")
        doc_content = gdocs.get_doc_content(doc_id)
        
        if dedup.is_duplicate(post.url, doc_content):
            return AgentResponse(status="skipped", reason="duplicate_url")
        
        response, markdown_content = agent.process_post(post)
        
        if response.status == "saved" and markdown_content:
            gdocs.append_to_doc(doc_id, markdown_content)
            
        return response
    except Exception as e:
        print(f"ERROR EN WEBHOOK: {e}")
        # Retornamos error con 200 OK para evitar que el webhook de Apify reintente automáticamente
        return AgentResponse(status="error", reason=str(e))
