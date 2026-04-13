# IA Intelligence Vault — Guía de Creación (Estado Actual → Producción)

> **The Architect** · Actualizado: 2026-04-13  
> Arquetipo: API Backend / AI Agent System  
> Stack: FastAPI + Python 3.11 + Claude Sonnet 4.6 + Google Docs API v1 + Railway

---

## Estado actual del proyecto

### ✅ Ya construido y funcional

| Archivo | Estado | Notas |
|---------|--------|-------|
| `app/main.py` | ✅ Completo | FastAPI, lifespan, /webhook, /health, auth |
| `app/agent.py` | ✅ Completo | Claude call, parse de respuesta, extracción de título |
| `app/models.py` | ✅ Completo | ApifyPost, AgentResponse (Pydantic v2) |
| `app/config.py` | ✅ Completo | Env vars, falla en startup si faltan |
| `services/gdocs.py` | ✅ Completo | get_or_create_doc, get_doc_content, append_to_doc |
| `services/dedup.py` | ✅ Completo | is_duplicate: url in doc_content |
| `prompts/system_prompt.md` | ✅ Completo | ROL del agente, leído en runtime |
| `requirements.txt` | ✅ Completo | Dependencias core |
| `requirements-dev.txt` | ✅ Completo | pytest, httpx, pytest-mock |
| `Procfile` | ✅ Completo | uvicorn con $PORT |
| `runtime.txt` | ✅ Completo | python-3.11.0 |
| `.env.example` | ✅ Completo | Las 4 env vars documentadas |
| `tests/test_agent.py` | ✅ Completo | Tests del clasificador con mock |
| `tests/test_dedup.py` | ✅ Completo | Tests de dedup |

### ❌ Falta construir

| Archivo | Prioridad | Por qué |
|---------|-----------|---------|
| `CLAUDE.md` | 🔴 CRÍTICO | Sin esto ningún agente puede retomar el proyecto |
| `README.md` | 🟡 IMPORTANTE | Documentación humana y onboarding |
| `tests/fixtures/post_technical.json` | 🟡 IMPORTANTE | Sin fixture los tests del webhook no pueden correr |
| `tests/fixtures/post_promo.json` | 🟡 IMPORTANTE | Ídem |
| `tests/fixtures/post_malformed.json` | 🔵 NICE TO HAVE | Caso borde de validación Pydantic |
| `tests/test_gdocs.py` | 🔵 NICE TO HAVE | Tests de dedup con doc content |
| `tests/test_webhook.py` | 🔵 NICE TO HAVE | Integration test del endpoint completo |

---

## PASO 1 — Crear `CLAUDE.md` (raíz del proyecto) 🔴 CRÍTICO

Crear el archivo `CLAUDE.md` en:
```
c:\Users\milag\OneDrive\Escritorio\estudio ig\ia-intelligence-vault\CLAUDE.md
```

Contenido exacto:

```markdown
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

## Model usado
- `claude-sonnet-4-6` — identificador exacto en la API de Anthropic (2026)
- `max_tokens=2048` — suficiente para el formato Markdown de 5 secciones

## Reglas No Negociables

1. **Nunca commitear credenciales.** `.env` en `.gitignore`. `GOOGLE_SERVICE_ACCOUNT_JSON` solo en Railway.
2. **Nunca llamar a Claude si el input está vacío.** Validar antes del LLM call — es dinero literal.
3. **Nunca hardcodear el nombre del Doc.** Constante en `config.py`, no esparcida en el código.
4. **El webhook siempre retorna 200 con JSON de status.** Nunca 500 — Apify puede reintentar y duplicar.
5. **Railway como único entorno de producción.** No Docker local para prod.
```

---

## PASO 2 — Crear `tests/fixtures/` con 3 archivos JSON

Crear el directorio `tests/fixtures/` dentro del proyecto.

### `tests/fixtures/post_technical.json`
```json
{
  "url": "https://www.instagram.com/p/C_EXAMPLE_TECH_001/",
  "ownerUsername": "ai_tools_es",
  "caption": "Probé Claude Computer Use y es una locura. Podés darle control total del navegador al modelo — hace clic, escribe, navega. El flujo: anthropic.messages.create() con tools=[{'type': 'computer_20241022', 'name': 'computer', 'display_width_px': 1920, 'display_height_px': 1080}]. Necesitás anthropic SDK >=0.37.0. Modelo: claude-3-5-sonnet-20241022. Repo: github.com/anthropics/anthropic-quickstarts",
  "timestamp": "2026-04-10T14:00:00Z",
  "videoTranscript": null
}
```

### `tests/fixtures/post_promo.json`
```json
{
  "url": "https://www.instagram.com/p/C_EXAMPLE_PROMO_001/",
  "ownerUsername": "curso_ia_gratis",
  "caption": "🔥 SORTEO 🔥 Sorteamos 3 lugares en nuestro curso de IA! Para participar: 1) Seguinos 2) Dale me gusta 3) Etiquetá a 2 amigos. Ganadores el viernes. ¡No te lo pierdas! 💪 #ia #sorteo #gratis",
  "timestamp": "2026-04-11T10:00:00Z",
  "videoTranscript": null
}
```

### `tests/fixtures/post_malformed.json`
```json
{
  "ownerUsername": "cuenta_sin_url",
  "caption": "Este post no tiene URL — debe fallar validación Pydantic"
}
```

---

## PASO 3 — Crear `tests/test_gdocs.py`

```python
"""Tests para services/dedup.py — lógica pura, sin mocks necesarios"""
import pytest
from services.dedup import is_duplicate


class TestIsNotDuplicate:
    def test_url_not_in_empty_doc(self):
        url = "https://instagram.com/p/ABC123/"
        assert not is_duplicate(url, "")

    def test_url_not_in_doc_with_other_content(self):
        url = "https://instagram.com/p/ABC123/"
        doc_content = "## Alguna herramienta\nhttps://instagram.com/p/XYZ999/"
        assert not is_duplicate(url, doc_content)


class TestIsDuplicate:
    def test_url_in_doc_content(self):
        url = "https://instagram.com/p/ABC123/"
        doc_content = f"## Claude Computer Use\n**Fuente:** @user\n{url}\n"
        assert is_duplicate(url, doc_content)

    def test_exact_url_match(self):
        url = "https://www.instagram.com/p/C_EXACT_MATCH/"
        assert is_duplicate(url, f"Procesado el 2026-04-10: {url}")
```

---

## PASO 4 — Crear `tests/test_webhook.py`

```python
"""Integration tests para POST /webhook — mockea Claude y Google API"""
import json
import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


def load_fixture(name: str) -> dict:
    path = Path(__file__).parent / "fixtures" / name
    return json.loads(path.read_text(encoding="utf-8"))


FAKE_SA = json.dumps({
    "type": "service_account", "project_id": "test", "private_key_id": "key1",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE==\n-----END RSA PRIVATE KEY-----\n",
    "client_email": "test@test.iam.gserviceaccount.com", "client_id": "123",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
})

ENV_PATCH = {
    "ANTHROPIC_API_KEY": "sk-ant-test",
    "GOOGLE_SERVICE_ACCOUNT_JSON": FAKE_SA,
    "GOOGLE_DRIVE_FOLDER_ID": "test-folder",
    "WEBHOOK_SECRET": "test-secret",
}

VALID_HEADERS = {"X-API-Key": "test-secret"}


@pytest.fixture(scope="module")
def client():
    with patch.dict(os.environ, ENV_PATCH):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestWebhookAuth:
    def test_no_key_returns_403(self, client):
        r = client.post("/webhook", json=load_fixture("post_technical.json"))
        assert r.status_code in (401, 403)

    def test_wrong_key_returns_401(self, client):
        r = client.post("/webhook", json=load_fixture("post_technical.json"),
                        headers={"X-API-Key": "wrong"})
        assert r.status_code == 401


class TestWebhookProcessing:
    def _mock_response(self, text: str):
        mock = MagicMock()
        mock.content = [MagicMock(text=text)]
        return mock

    def test_promo_post_skipped(self, client):
        skip_json = '{"status": "skipped", "reason": "no_technical_content"}'
        with patch("app.agent.Anthropic") as m, \
             patch("services.gdocs.get_or_create_doc", return_value="doc-id"), \
             patch("services.gdocs.get_doc_content", return_value=""), \
             patch("services.gdocs.append_to_doc"):
            m.return_value.messages.create.return_value = self._mock_response(skip_json)
            r = client.post("/webhook", json=load_fixture("post_promo.json"), headers=VALID_HEADERS)
        assert r.status_code == 200
        assert r.json()["status"] == "skipped"

    def test_technical_post_saved(self, client):
        md = "---\n## Claude Computer Use\n\n| Campo | Valor |\n|---|---|\n| **Fuente** | @ai_tools_es |\n\n### Núcleo Técnico\nControl de navegador via API.\n\n---"
        with patch("app.agent.Anthropic") as m, \
             patch("services.gdocs.get_or_create_doc", return_value="doc-id"), \
             patch("services.gdocs.get_doc_content", return_value=""), \
             patch("services.gdocs.append_to_doc") as mock_append:
            m.return_value.messages.create.return_value = self._mock_response(md)
            r = client.post("/webhook", json=load_fixture("post_technical.json"), headers=VALID_HEADERS)
            mock_append.assert_called_once()
        assert r.status_code == 200
        assert r.json()["status"] == "saved"
        assert r.json()["doc"] == "IA_Intelligence_Vault"

    def test_duplicate_skipped(self, client):
        post = load_fixture("post_technical.json")
        with patch("services.gdocs.get_or_create_doc", return_value="doc-id"), \
             patch("services.gdocs.get_doc_content", return_value=post["url"]):
            r = client.post("/webhook", json=post, headers=VALID_HEADERS)
        assert r.json()["status"] == "skipped"
        assert r.json()["reason"] == "duplicate_url"
```

---

## PASO 5 — Crear `README.md`

```markdown
# IA Intelligence Vault

Pipeline de inteligencia técnica automatizado. Recibe JSON de Apify (scraping de Instagram),
clasifica con Claude Sonnet 4.6, y persiste entradas estructuradas en Google Docs.

## Flujo

```
Apify → POST /webhook → Claude clasifica → Google Doc "IA_Intelligence_Vault"
```

## Setup local

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
copy .env.example .env        # Editar con valores reales
uvicorn app.main:app --reload
```

## Testear el webhook localmente

```bash
curl -X POST http://localhost:8000/webhook ^
  -H "X-API-Key: tu_webhook_secret" ^
  -H "Content-Type: application/json" ^
  -d @tests/fixtures/post_technical.json
```

## Tests

```bash
pytest tests/ -v
```

## Variables de entorno

| Variable | Cómo obtenerla |
|----------|----------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google Cloud → IAM → Service Accounts → Keys → Add Key (JSON) |
| `GOOGLE_DRIVE_FOLDER_ID` | URL del folder: `drive.google.com/drive/folders/{FOLDER_ID}` |
| `WEBHOOK_SECRET` | `python -c "import secrets; print(secrets.token_hex(32))"` |

## Deploy en Railway

1. Push del repo a GitHub
2. Railway → New Project → Deploy from GitHub
3. Settings → Variables → agregar las 4 env vars
4. Railway detecta `requirements.txt` + `Procfile` automáticamente

**Convertir GOOGLE_SERVICE_ACCOUNT_JSON a una línea:**
```bash
cat service-account.json | python -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
```

## Configurar Apify Webhook

En Apify Console → tu Actor → Webhooks:
- **URL:** `https://tu-proyecto.railway.app/webhook`
- **Method:** POST
- **Header:** `X-API-Key: {tu WEBHOOK_SECRET}`
- **Event:** `ACTOR.RUN.SUCCEEDED`
```

---

## Checklist de verificación final

Antes de declarar el proyecto completo:

- [ ] `CLAUDE.md` creado en la raíz
- [ ] `README.md` creado en la raíz
- [ ] `tests/fixtures/post_technical.json` creado
- [ ] `tests/fixtures/post_promo.json` creado
- [ ] `tests/fixtures/post_malformed.json` creado
- [ ] `tests/test_gdocs.py` creado
- [ ] `tests/test_webhook.py` creado
- [ ] `pytest tests/ -v` corre sin errores
- [ ] `uvicorn app.main:app --reload` arranca sin errores
- [ ] `curl http://localhost:8000/health` → `{"status": "ok"}`
- [ ] Webhook local con fixture técnico → `{"status": "saved"}`
- [ ] Webhook local con fixture promo → `{"status": "skipped"}`
- [ ] Railway tiene las 4 env vars configuradas
- [ ] Apify webhook apunta a Railway con el header correcto

---

## Estructura final del proyecto

```
ia-intelligence-vault/
  app/
    main.py          ✅ FastAPI, /webhook, /health, auth
    agent.py         ✅ Claude call, parse, title extraction
    models.py        ✅ ApifyPost, AgentResponse
    config.py        ✅ Settings con env vars
  services/
    gdocs.py         ✅ Google Docs API
    dedup.py         ✅ is_duplicate(url, content)
  prompts/
    system_prompt.md ✅ ROL del agente
  tests/
    fixtures/
      post_technical.json   ❌ → PASO 2
      post_promo.json       ❌ → PASO 2
      post_malformed.json   ❌ → PASO 2
    test_agent.py    ✅
    test_dedup.py    ✅
    test_gdocs.py    ❌ → PASO 3
    test_webhook.py  ❌ → PASO 4
  .env.example       ✅
  Procfile           ✅
  runtime.txt        ✅
  requirements.txt   ✅
  requirements-dev.txt ✅
  CLAUDE.md          ❌ → PASO 1 (CRÍTICO)
  README.md          ❌ → PASO 5
```
