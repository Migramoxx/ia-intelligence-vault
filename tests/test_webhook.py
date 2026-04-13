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
    "type": "service_account",
    "project_id": "test",
    "private_key_id": "key1",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE==\n-----END RSA PRIVATE KEY-----\n",
    "client_email": "test@test.iam.gserviceaccount.com",
    "client_id": "123",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
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
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestWebhookAuth:
    def test_no_key_returns_403_or_401(self, client):
        r = client.post("/webhook", json=load_fixture("post_technical.json"))
        assert r.status_code in (401, 403)

    def test_wrong_key_returns_401(self, client):
        r = client.post(
            "/webhook",
            json=load_fixture("post_technical.json"),
            headers={"X-API-Key": "wrong-key"},
        )
        assert r.status_code == 401


class TestWebhookProcessing:
    def _mock_claude_response(self, text: str) -> MagicMock:
        mock = MagicMock()
        mock.content = [MagicMock(text=text)]
        return mock

    def test_promo_post_returns_skipped(self, client):
        skip_json = '{"status": "skipped", "reason": "no_technical_content"}'
        with (
            patch("app.agent.Anthropic") as mock_anthropic,
            patch("services.gdocs.get_or_create_doc", return_value="doc-id"),
            patch("services.gdocs.get_doc_content", return_value=""),
            patch("services.gdocs.append_to_doc"),
        ):
            mock_anthropic.return_value.messages.create.return_value = (
                self._mock_claude_response(skip_json)
            )
            r = client.post(
                "/webhook",
                json=load_fixture("post_promo.json"),
                headers=VALID_HEADERS,
            )
        assert r.status_code == 200
        assert r.json()["status"] == "skipped"

    def test_technical_post_returns_saved(self, client):
        markdown = (
            "---\n## Claude Computer Use\n\n"
            "| Campo | Valor |\n|---|---|\n"
            "| **Fuente** | @ai_tools_es |\n"
            "| **Fecha** | 2026-04-10 |\n"
            "| **Categoría** | BIG_TECH_UPDATE |\n\n"
            "### Núcleo Técnico\nControl de navegador via API. El modelo hace clic y escribe.\n\n"
            "### Implementación\n- Instalar anthropic SDK >=0.37.0\n- Usar tools=[{'type': 'computer_20241022'}]\n\n"
            "---"
        )
        with (
            patch("app.agent.Anthropic") as mock_anthropic,
            patch("services.gdocs.get_or_create_doc", return_value="doc-id"),
            patch("services.gdocs.get_doc_content", return_value=""),
            patch("services.gdocs.append_to_doc") as mock_append,
        ):
            mock_anthropic.return_value.messages.create.return_value = (
                self._mock_claude_response(markdown)
            )
            r = client.post(
                "/webhook",
                json=load_fixture("post_technical.json"),
                headers=VALID_HEADERS,
            )
            mock_append.assert_called_once()

        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "saved"
        assert body["doc"] == "IA_Intelligence_Vault"

    def test_duplicate_url_returns_skipped(self, client):
        post = load_fixture("post_technical.json")
        # El doc content ya contiene la URL del post → debe ser skip
        with (
            patch("services.gdocs.get_or_create_doc", return_value="doc-id"),
            patch("services.gdocs.get_doc_content", return_value=post["url"]),
        ):
            r = client.post("/webhook", json=post, headers=VALID_HEADERS)

        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "skipped"
        assert body["reason"] == "duplicate_url"
