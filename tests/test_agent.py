"""Tests del agente Claude — mockea la llamada a Anthropic API"""
from unittest.mock import patch, MagicMock
from app.models import ApifyPost


def _make_claude_mock(text: str) -> MagicMock:
    """Helper: crea un mock de anthropic.messages.create con texto dado."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=text)]
    return mock_response


def _make_post(caption: str = None, transcript: str = None) -> ApifyPost:
    return ApifyPost(
        url="https://www.instagram.com/p/C_TEST_001/",
        ownerUsername="test_user",
        caption=caption,
        timestamp="2026-04-10T14:00:00Z",
        videoTranscript=transcript,
    )


class TestProcessPostSkipped:
    def test_promo_post_returns_skipped(self):
        skip_json = '{"status": "skipped", "reason": "no_technical_content"}'
        with patch("app.agent.Anthropic") as mock_anth:
            mock_anth.return_value.messages.create.return_value = (
                _make_claude_mock(skip_json)
            )
            from app.agent import process_post
            response, content = process_post(_make_post(caption="Sorteo gratis! Seguinos"))

        assert response.status == "skipped"
        assert response.reason == "no_technical_content"
        assert content is None

    def test_skipped_wrapped_in_json_code_block(self):
        """Claude a veces envuelve el JSON en ```json ... ```"""
        skip_json = '```json\n{"status": "skipped", "reason": "no_technical_content"}\n```'
        with patch("app.agent.Anthropic") as mock_anth:
            mock_anth.return_value.messages.create.return_value = (
                _make_claude_mock(skip_json)
            )
            from app.agent import process_post
            response, content = process_post(_make_post(caption="Sorteo gratis!"))

        assert response.status == "skipped"
        assert content is None


class TestProcessPostSaved:
    def test_technical_post_returns_saved_with_markdown(self):
        markdown = (
            "---\n## Claude Computer Use\n\n"
            "| Campo | Valor |\n|---|---|\n"
            "| **Fuente** | @ai_tools_es |\n"
            "| **Fecha** | 2026-04-10 |\n"
            "| **Categoría** | BIG_TECH_UPDATE |\n\n"
            "### Núcleo Técnico\nControl de navegador via API.\n\n"
            "### Implementación\n- Instalar anthropic SDK\n\n---"
        )
        with patch("app.agent.Anthropic") as mock_anth:
            mock_anth.return_value.messages.create.return_value = (
                _make_claude_mock(markdown)
            )
            from app.agent import process_post
            response, content = process_post(
                _make_post(caption="Claude Computer Use lanzado. Controla el navegador vía API.")
            )

        assert response.status == "saved"
        assert response.doc == "IA_Intelligence_Vault"
        assert response.title is not None
        assert "Claude Computer Use" in response.title
        assert content is not None
        assert "## Claude Computer Use" in content

    def test_title_extracted_from_markdown_h2(self):
        markdown = "---\n## Mi Herramienta Técnica\n\n### Núcleo Técnico\nAlgo útil.\n---"
        with patch("app.agent.Anthropic") as mock_anth:
            mock_anth.return_value.messages.create.return_value = (
                _make_claude_mock(markdown)
            )
            from app.agent import process_post
            response, _ = process_post(_make_post(caption="Herramienta técnica útil"))

        assert response.title == "Mi Herramienta Técnica"
