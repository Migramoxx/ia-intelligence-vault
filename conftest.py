import sys
import os
import json

# 1. Agrega la raíz del proyecto al PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

# 2. Inyecta env vars de test ANTES de que cualquier módulo del proyecto
#    sea importado, para que config.py pueda instanciar Settings() sin error.
_FAKE_SA = json.dumps({
    "type": "service_account",
    "project_id": "test",
    "private_key_id": "key1",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE==\n-----END RSA PRIVATE KEY-----\n",
    "client_email": "test@test.iam.gserviceaccount.com",
    "client_id": "123",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
})

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", _FAKE_SA)
os.environ.setdefault("GOOGLE_DRIVE_FOLDER_ID", "test-folder-id")
os.environ.setdefault("WEBHOOK_SECRET", "test-secret")
