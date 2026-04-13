from fastapi import FastAPI, Depends, HTTPException, Security, Request
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
async def webhook(request: Request, api_key: str = Depends(get_api_key)):
    try:
        body_bytes = await request.body()
        print(f"DEBUG RAW BODY: {body_bytes.decode('utf-8', errors='replace')}")
        
        data = await request.json()
        post = ApifyPost(**data)
        
        if not post.caption and not post.videoTranscript:
            return AgentResponse(status="error", reason="invalid_input")

        print(f"DEBUG: Processing post {post.url}")
        
        doc_id = gdocs.get_or_create_doc("IA_Intelligence_Vault")
        print(f"DEBUG: Target Doc ID: {doc_id}")
        
        doc_content = gdocs.get_doc_content(doc_id)
        
        if dedup.is_duplicate(post.url, doc_content):
            print(f"DEBUG: Skipping duplicate post: {post.url}")
            return AgentResponse(status="skipped", reason="duplicate_url")
        
        print("DEBUG: Calling Claude agent...")
        response, markdown_content = agent.process_post(post)
        print(f"DEBUG: Agent response status: {response.status}")
        
        if response.status == "saved" and markdown_content:
            print("DEBUG: Appending insights to Google Doc...")
            gdocs.append_to_doc(doc_id, markdown_content)
            print("DEBUG: Success!")
        else:
            print(f"DEBUG: No insight saved. Reason: {response.reason}")
            
        return response
    except Exception as e:
        print(f"ERROR EN WEBHOOK: {e}")
        return AgentResponse(status="error", reason=str(e))
