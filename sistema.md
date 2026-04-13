¡Excelente! Me pongo el traje de The Architect 🏗️. He leído el archivo promp a seguir.md. Entiendo perfectamente la visión: estamos diseñando un pipeline de Inteligencia Técnica (un agente automatizado) que recibe datos scrapeados de Apify (posts y reels de Instagram), utiliza IA para limpiar el ruido y extraer únicamente el valor duro/técnico, y alinea esa información como una base de conocimiento acumulativa en Google Docs. Para la metodología de The Architect, esto clasifica en el arquetipo de Herramienta Interna / Backend Automation (internal-tool / api-backend). Para terminar de definir los componentes antes de armar el blueprint, necesito hacerte 3 preguntas clave:





Orquestación: Para conectar el Webhook/JSON de Apify, la IA y Google Drive de manera fluida, ¿planeás usar n8n como motor principal de esta automatización? (Veo que tenés abierto tu entorno local de n8n, lo cual sería ideal).



El "Cerebro" (LLM): Para los pasos de clasificación (Paso 2), anti-redundancia (Paso 3) y formateo estricto del JSON a Markdown (Paso 4), ¿qué modelo de lenguaje preferís usar? (ej. OpenAI gpt-4o, Anthropic claude-3-5-sonnet, Google gemini-1.5-pro).



Frecuencia/Escala: ¿Este agente va a recibir llamadas vía Webhook una por una en tiempo real cada vez que Apify procesa un post, o va a correr por "lotes" (ej. procesar un JSON con 50 posts de golpe una vez a la semana)? Respondeme y armamos la estructura técnica exacta.



respuestas 

1. Orquestación: No, n8n no va a ser el motor principal. El pipeline corre sobre Claude Managed Agents vía API (Anthropic Console). n8n puede quedar como disparador opcional si ya lo tenés corriendo, pero no es una dependencia del sistema.

2. Cerebro: Claude Sonnet 4.6 — es el modelo que ya está configurado en el agente y tiene el mejor balance costo/calidad para clasificación semántica y formateo estricto en 2026.

3. Frecuencia: Webhook en tiempo real, un post por llamada. Apify dispara al agente cada vez que completa el scraping de un post. No queremos lotes — el vault crece solo sin intervención manual.





Perfecto. Tengo todo lo que necesito. Antes de generar, te presento la arquitectura propuesta para tu confirmación: Arquitectura Propuesta — IA Intelligence Vault Agent Arquetipo: API Backend / AI Agent System CapaTecnologíaRazónMotor de agenteClaude Sonnet 4.6 (Anthropic API)Clasificación semántica + formateo estricto en un solo LLM callRuntimePython 3.11 (FastAPI)Ecosistema de IA nativo, integración directa con Anthropic SDKWebhook endpointFastAPI + UvicornRecibe el POST de Apify en tiempo realGoogle DriveGoogle Docs API v1 (Service Account)Append sin fricción, sin OAuth interactivoDeduplicaciónRedis (Upstash)Cache de URLs procesadas, lookup O(1)DeployRailway (o Fly.io)Simple, barato, soporte nativo para PythonValidación inputPydantic v2Parseo estricto del JSON de Apify Flujo exacto:

Apify → POST /webhook → Pydantic valida → Redis check (dedup)

  → Claude clasifica + extrae + formatea    → Google Docs API append → {"status": "saved"} Componentes críticos:





POST /webhook — endpoint único que recibe el JSON de Apify



agent/classifier.py — llama a Claude con el system prompt de tu archivo promp a seguir.md



services/gdocs.py — busca/crea "IA_Intelligence_Vault" y hace append



services/dedup.py — Redis SET para trackear URLs procesadas Una última pregunta antes de generar el blueprint completo: ¿Querés que el CLAUDE.md del proyecto incluya instrucciones para que el agente constructor levante la Google Service Account con variables de entorno, o ya tenés un flujo de autenticación de Google Drive preferido (OAuth, ADC, service account JSON)?



respuesta

Service Account con variables de entorno — seteá las credenciales como env vars en Railway, no como archivo JSON commiteado. El CLAUDE.md debe incluir instrucciones para leer GOOGLE_SERVICE_ACCOUNT_JSON (el JSON completo como string) y GOOGLE_DRIVE_FOLDER_ID desde el entorno.

Una aclaración sobre la arquitectura: la propuesta está bien estructurada pero tiene una capa de más para tu caso. Redis/Upstash para dedup es overkill si el volumen es una cuenta de IG. Reemplazalo por un Set en memoria o simplemente que el agente busque la URL en el Doc antes de escribir — cero infraestructura adicional, mismo resultado.

El stack final que apruebo:





FastAPI + Uvicorn ✅



Claude Sonnet 4.6 ✅



Google Docs API v1 con Service Account ✅



Railway ✅



Redis ❌ → reemplazar por búsqueda de URL en el Doc (ya está en el system prompt)



Blueprint generado y guardado en: C:\Users\milag\.gemini\antigravity\skills\the-architect\output\ia-intelligence-vault-blueprint.md Resumen de lo que contiene:





Stack aprobado: FastAPI + Python 3.11 + Claude Sonnet 4.6 + Google Docs API v1 + Railway. Sin Redis.



Dedup sin infraestructura: is_duplicate es literalmente return url in doc_content — el Doc es la fuente de verdad.



12 pasos de build ordenados, desde mkdir hasta configurar el webhook en Apify.



CLAUDE.md completo para que cualquier agente de código construya el sistema desde cero sin preguntas, incluyendo el snippet exacto para parsear GOOGLE_SERVICE_ACCOUNT_JSON en Railway.



7 reglas no negociables, la más importante: nunca llamar a Claude si el input está vacío (protección de tokens). 

@contextScopeItemMention 

elabora la guia de implementacion para crear el proyecto a partir de donde dejamos el proyecto ia_intelligence-vault. 