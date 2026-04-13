# IA Intelligence Vault Agent

Pipeline de inteligencia técnica: recibe JSON de Apify (posts de Instagram),
clasifica con Claude Sonnet 4.6, persiste entradas Markdown en Google Docs.

## Commands

- `uvicorn app.main:app --reload` — Desarrollo local (puerto 8000)
- `pytest tests/ -v` — Correr todos los tests
- `pip install -r requirements.txt` — Instalar dependencias core
- `pip install -r requirements-dev.txt` — Instalar dependencias de dev

## Tech Stack

FastAPI + Python 3.11 + Anthropic SDK + Google Docs API v1 + Railway

## Architecture

### Data Flow
```
POST /webhook → Pydantic valida ApifyPost
  → gdocs.get_or_create_doc() → gdocs.get_doc_content()
  → dedup.is_duplicate(url, content) → [skip si True]
  → agent.process_post(post) → Claude clasifica + formatea
  → gdocs.append_to_doc(doc_id, markdown)
  → return AgentResponse
```

### Directory Structure
- `app/main.py` — FastAPI app, endpoint /webhook, /health, auth dependency
- `app/agent.py` — Llama a Claude, retorna Markdown o skipped JSON
- `app/models.py` — Pydantic: ApifyPost (input), AgentResponse (output)
- `app/config.py` — Lee env vars, valida en startup, expone Settings singleton
- `services/gdocs.py` — Google Docs API: get_or_create_doc, get_doc_content, append_to_doc
- `services/dedup.py` — is_duplicate(url, content): retorna True si url in content
- `prompts/system_prompt.md` — ROL del agente, leído en runtime por agent.py

### Key Patterns
- El system prompt se lee desde archivo en runtime (no hardcodeado) para cambios sin redeploy
- El `doc_id` del vault se cachea en memoria en `services/gdocs.py` — una sola búsqueda por proceso
- Claude recibe el JSON del post completo como user message; la respuesta ES el Markdown final
- Dedup es `url in doc_content` — el Doc es la única source of truth

## Code Organization Rules

1. **Un archivo por responsabilidad.** `agent.py` no toca Google Docs. `gdocs.py` no llama a Claude.
2. **Toda llamada externa mockeable.** Las funciones de `gdocs.py` y `agent.py` son mockeables en tests.
3. **Config centralizada.** Todas las env vars se leen en `app/config.py`. Nunca `os.environ` directo.
4. **Falla rápido en startup.** Si una env var falta, el proceso no arranca — mejor error claro al inicio.
5. **Sin estado mutable global excepto `doc_id`.** El cache en gdocs.py es la única excepción.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key de Anthropic Console |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSON completo de la service account como string (una línea) |
| `GOOGLE_DRIVE_FOLDER_ID` | ID del folder de Drive (de la URL: drive.google.com/drive/folders/{ID}) |
| `WEBHOOK_SECRET` | API key para proteger POST /webhook (header X-API-Key) |

**Para Railway:** Setear todas en Settings → Variables. NUNCA commitear `.env`.
**Para LOCAL:** Crear `.env` basado en `.env.example`. `python-dotenv` lo carga automáticamente.

**Parsing de GOOGLE_SERVICE_ACCOUNT_JSON en config.py:**
```python
import json, os
service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
credentials = Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/drive.readonly"]
)
```

## Model usado
- `claude-sonnet-4-6` — identificador exacto en la API de Anthropic (2026)
- `max_tokens=2048` — suficiente para el formato Markdown de 5 secciones

## Reglas No Negociables

1. **Nunca commitear credenciales.** `.env` en `.gitignore`. `GOOGLE_SERVICE_ACCOUNT_JSON` solo en Railway.
2. **Nunca llamar a Claude si el input está vacío.** Validar antes del LLM call — es dinero literal.
3. **Nunca hardcodear el nombre del Doc.** Constante en `config.py`, no esparcida en el código.
4. **El webhook siempre retorna 200 con JSON de status.** Nunca 500 — Apify puede reintentar y duplicar.
5. **Railway como único entorno de producción.** No Docker local para prod.
