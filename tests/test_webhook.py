"""Tests de integración del webhook — flujo completo con payload de Apify."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


APIFY_WEBHOOK_PAYLOAD = {
    "resource": {
        "defaultDatasetId": "test-dataset-abc123"
    }
}

DATASET_ITEMS_TECHNICAL = [
    {
        "url": "https://www.instagram.com/p/C_TECH_001/",
        "ownerUsername": "soyenriquerocha",
        "caption": "Claude Computer Use lanzado. Controla el navegador vía API con pip install anthropic>=0.37.0",
        "timestamp": "2026-04-10T14:00:00Z",
    }
]

DATASET_ITEMS_PROMO = [
    {
        "url": "https://www.instagram.com/p/C_PROMO_001/",
        "ownerUsername": "agustinbadt",
        "caption": "Sorteo gratis! Seguime y ganate productos top.",
        "timestamp": "2026-04-10T15:00:00Z",
    }
]

DATASET_ITEMS_MIXED = [
    {
        "url": "https://www.instagram.com/p/C_TECH_002/",
        "ownerUsername": "miguelbaenaia",
        "caption": "GPT-4o con vision puede analizar diagramas de código en tiempo real.",
        "timestamp": "2026-04-10T16:00:00Z",
    },
    {
        "url": "https://www.instagram.com/p/C_PROMO_002/",
        "ownerUsername": "fabriguaglianone",
        "caption": "¡Nuevo curso disponible! Descuento por tiempo limitado.",
        "timestamp": "2026-04-10T17:00:00Z",
    },
]

MARKDOWN_SAVED = (
    "---\n## Claude Computer Use\n\n"
    "| Campo | Valor |\n|---|---|\n"
    "| **Fuente** | @soyenriquerocha |\n\n"
    "### Núcleo Técnico\nAPI de control de navegador.\n---"
)


def _make_client():
    from app.main import app
    return TestClient(app)


class TestHealth:
    def test_health_returns_ok_with_profiles(self):
        client = _make_client()
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "monitored_profiles" in body
        assert "soyenriquerocha" in body["monitored_profiles"]


class TestWebhookAuth:
    def test_no_key_returns_401(self):
        client = _make_client()
        r = client.post("/webhook", json=APIFY_WEBHOOK_PAYLOAD)
        assert r.status_code in (401, 403)

    def test_wrong_key_returns_401(self):
        client = _make_client()
        r = client.post(
            "/webhook",
            json=APIFY_WEBHOOK_PAYLOAD,
            headers={"X-API-Key": "wrong-key"},
        )
        assert r.status_code == 401


class TestWebhookProcessing:
    def _post(self, items: list, doc_content: str = ""):
        """Helper: envía webhook con dataset mockeado."""
        client = _make_client()
        with (
            patch("services.apify.fetch_dataset_items", return_value=items),
            patch("services.gdocs.get_or_create_doc", return_value="doc-id-123"),
            patch("services.gdocs.get_doc_content", return_value=doc_content),
            patch("services.gdocs.append_to_doc") as mock_append,
            patch("app.agent.Anthropic") as mock_anth,
        ):
            mock_anth.return_value.messages.create.return_value = MagicMock(
                content=[MagicMock(text=MARKDOWN_SAVED)]
            )
            response = client.post(
                "/webhook",
                json=APIFY_WEBHOOK_PAYLOAD,
                headers={"X-API-Key": "test-secret"},
            )
            return response, mock_append

    def test_technical_post_is_saved(self):
        r, mock_append = self._post(DATASET_ITEMS_TECHNICAL)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["saved"] == 1
        assert body["skipped"] == 0
        mock_append.assert_called_once()

    def test_promo_post_is_skipped_by_agent(self):
        skip_response = MagicMock()
        skip_response.content = [MagicMock(text='{"status": "skipped", "reason": "no_technical_content"}')]
        client = _make_client()
        with (
            patch("services.apify.fetch_dataset_items", return_value=DATASET_ITEMS_PROMO),
            patch("services.gdocs.get_or_create_doc", return_value="doc-id-123"),
            patch("services.gdocs.get_doc_content", return_value=""),
            patch("services.gdocs.append_to_doc") as mock_append,
            patch("app.agent.Anthropic") as mock_anth,
        ):
            mock_anth.return_value.messages.create.return_value = skip_response
            r = client.post(
                "/webhook",
                json=APIFY_WEBHOOK_PAYLOAD,
                headers={"X-API-Key": "test-secret"},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["saved"] == 0
        assert body["skipped"] == 1
        mock_append.assert_not_called()

    def test_duplicate_post_is_skipped(self):
        existing_content = "https://www.instagram.com/p/C_TECH_001/"
        r, mock_append = self._post(DATASET_ITEMS_TECHNICAL, doc_content=existing_content)
        assert r.status_code == 200
        body = r.json()
        assert body["skipped"] == 1
        assert body["saved"] == 0
        mock_append.assert_not_called()

    def test_mixed_dataset_summary(self):
        """Dataset con 1 técnico + 1 promo: saved=1, skipped=1."""
        skip_markdown = MARKDOWN_SAVED  # técnico
        skip_json = '{"status": "skipped", "reason": "no_technical_content"}'
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            text = skip_markdown if call_count == 1 else skip_json
            return MagicMock(content=[MagicMock(text=text)])

        client = _make_client()
        with (
            patch("services.apify.fetch_dataset_items", return_value=DATASET_ITEMS_MIXED),
            patch("services.gdocs.get_or_create_doc", return_value="doc-id-123"),
            patch("services.gdocs.get_doc_content", return_value=""),
            patch("services.gdocs.append_to_doc"),
            patch("app.agent.Anthropic") as mock_anth,
        ):
            mock_anth.return_value.messages.create.side_effect = side_effect
            r = client.post(
                "/webhook",
                json=APIFY_WEBHOOK_PAYLOAD,
                headers={"X-API-Key": "test-secret"},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2

    def test_empty_dataset_returns_zero_total(self):
        r, _ = self._post([])
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_invalid_apify_payload_returns_error(self):
        client = _make_client()
        r = client.post(
            "/webhook",
            json={"wrong": "format"},
            headers={"X-API-Key": "test-secret"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "error"
