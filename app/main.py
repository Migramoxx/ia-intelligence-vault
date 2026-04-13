from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from contextlib import asynccontextmanager
from pydantic import ValidationError

from app.config import settings
from app.models import ApifyPost, ApifyWebhookPayload, AgentResponse, BatchResponse
from services import gdocs, dedup, apify as apify_service
from app import agent

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.webhook_secret:
        return api_key_header
    raise HTTPException(status_code=401, detail="Invalid API Key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = settings.anthropic_api_key
    _ = settings.apify_token
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    profiles = settings.instagram_profiles.split(",")
    return {
        "status": "ok",
        "version": "2.0.0",
        "monitored_profiles": [p.strip() for p in profiles],
    }


@app.post("/webhook", response_model=BatchResponse)
async def webhook(request: Request, api_key: str = Depends(get_api_key)):
    """
    Recibe el payload de Apify cuando un Actor run finaliza con éxito.
    Descarga el dataset completo y procesa cada post de Instagram.
    
    Payload esperado de Apify:
    {
        "resource": {
            "defaultDatasetId": "abc123..."
        }
    }
    """
    result = BatchResponse()

    try:
        data = await request.json()
        print(f"DEBUG RAW BODY: {data}")

        # Parsear el payload de Apify
        try:
            payload = ApifyWebhookPayload(**data)
        except ValidationError as ve:
            print(f"ERROR: Payload de Apify inválido: {ve}")
            return BatchResponse(status="error", errors=1)

        dataset_id = payload.resource.defaultDatasetId
        print(f"DEBUG: Fetching dataset {dataset_id} from Apify...")

        # Descargar items del dataset
        items = apify_service.fetch_dataset_items(dataset_id)
        result.total = len(items)
        print(f"DEBUG: {result.total} posts encontrados en el dataset.")

        if not items:
            return BatchResponse(status="ok", total=0)

        # Obtener o crear el Google Doc de destino
        doc_id = gdocs.get_or_create_doc("IA_Intelligence_Vault")
        print(f"DEBUG: Target Doc ID: {doc_id}")

        # Procesar cada post en loop
        for item in items:
            try:
                post = ApifyPost(**item)
            except (ValidationError, Exception) as e:
                print(f"WARN: Post inválido, se omite. Error: {e}")
                result.errors += 1
                continue

            # Saltar si no hay contenido para analizar
            if not post.caption and not post.videoTranscript:
                print(f"DEBUG: Post sin caption/transcript, omitiendo: {post.url}")
                result.skipped += 1
                continue

            # Deduplicación
            doc_content = gdocs.get_doc_content(doc_id)
            if dedup.is_duplicate(post.url, doc_content):
                print(f"DEBUG: Duplicado, omitiendo: {post.url}")
                result.skipped += 1
                continue

            # Clasificar con Claude
            print(f"DEBUG: Procesando @{post.ownerUsername}: {post.url}")
            response, markdown_content = agent.process_post(post)

            if response.status == "saved" and markdown_content:
                gdocs.append_to_doc(doc_id, markdown_content)
                result.saved += 1
                print(f"DEBUG: ✓ Guardado: {response.title}")
            else:
                result.skipped += 1
                print(f"DEBUG: Omitido por Claude: {response.reason}")

        print(f"DEBUG RESUMEN: total={result.total}, saved={result.saved}, skipped={result.skipped}, errors={result.errors}")
        return result

    except Exception as e:
        print(f"ERROR EN WEBHOOK: {e}")
        return BatchResponse(status="error", errors=1)
