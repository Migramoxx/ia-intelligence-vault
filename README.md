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
copy .env.example .env        # Editar .env con valores reales
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
2. Railway → New Project → Deploy from GitHub → seleccionar el repo
3. Settings → Variables → agregar las 4 env vars
4. Railway detecta `requirements.txt` + `Procfile` automáticamente — no hay nada más que hacer

**⚠️ Convertir GOOGLE_SERVICE_ACCOUNT_JSON a una línea antes de pegarlo en Railway:**
```bash
cat service-account.json | python -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
```

## Configurar Apify Webhook

En Apify Console → tu Actor → Webhooks:
- **URL:** `https://tu-proyecto.railway.app/webhook`
- **Method:** POST
- **Header:** `X-API-Key: {tu WEBHOOK_SECRET}`
- **Event:** `ACTOR.RUN.SUCCEEDED`

## Output esperado en el Google Doc

```markdown
---
## Claude Computer Use

| Campo | Valor |
|---|---|
| **Fuente** | @ai_tools_es |
| **Fecha** | 2026-04-10 |
| **Categoría** | BIG_TECH_UPDATE |
| **Dependencias** | API Key |
| **Confianza** | Alta |

### Núcleo Técnico
Control total del navegador vía API. El modelo hace clic, escribe y navega de forma autónoma.

### Implementación
- Instalar anthropic SDK >=0.37.0
- Usar tools=[{'type': 'computer_20241022'}] en el messages.create()

### Recursos
- **Repo/URL:** github.com/anthropics/anthropic-quickstarts
- **Versión/Modelo:** claude-3-5-sonnet-20241022

---
```
