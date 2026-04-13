"""Tests del cliente de Apify API."""
from unittest.mock import patch, MagicMock


SAMPLE_ITEMS = [
    {
        "url": "https://www.instagram.com/p/C_TEST_001/",
        "ownerUsername": "soyenriquerocha",
        "caption": "Claude Computer Use permite controlar el navegador vía API. Instalar con pip install anthropic>=0.37.0",
        "timestamp": "2026-04-10T14:00:00Z",
    },
    {
        "url": "https://www.instagram.com/p/C_TEST_002/",
        "ownerUsername": "agustinbadt",
        "caption": "Sorteo de productos gratis. Seguime!",
        "timestamp": "2026-04-10T15:00:00Z",
    },
    {
        # Post sin URL pero con shortCode
        "shortCode": "C_TEST_003",
        "ownerUsername": "miguelbaenaia",
        "caption": "GPT-4o con vision ahora puede analizar código en tiempo real.",
        "timestamp": "2026-04-10T16:00:00Z",
    },
]


def test_fetch_dataset_items_success():
    """Debe llamar a la URL correcta y retornar los items."""
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_ITEMS
    mock_response.raise_for_status = MagicMock()

    with patch("services.apify.httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.get.return_value = mock_response

        from services.apify import fetch_dataset_items
        items = fetch_dataset_items("test-dataset-id")

    assert len(items) == 3
    assert items[0]["ownerUsername"] == "soyenriquerocha"
    mock_client.get.assert_called_once()

    # Verificar que usa el token correcto
    call_kwargs = mock_client.get.call_args
    assert "test-dataset-id" in call_kwargs[0][0]
    assert call_kwargs[1]["params"]["token"] == "apify_test_token"


def test_fetch_dataset_items_empty():
    """Dataset vacío retorna lista vacía."""
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()

    with patch("services.apify.httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.get.return_value = mock_response

        from services.apify import fetch_dataset_items
        items = fetch_dataset_items("empty-dataset")

    assert items == []


def test_post_normalizes_shortcode_to_url():
    """ApifyPost debe construir URL desde shortCode si no viene url directa."""
    from app.models import ApifyPost

    post = ApifyPost(**{
        "shortCode": "C_ABC123",
        "ownerUsername": "miguelbaenaia",
        "caption": "Algo técnico aquí",
    })

    assert post.url == "https://www.instagram.com/p/C_ABC123/"


def test_post_normalizes_transcript_extractor_format():
    """ApifyPost debe mapear campos del Transcript Extractor al schema unificado."""
    from app.models import ApifyPost

    raw = {
        "url": "https://www.instagram.com/p/C_XYZ/",
        "ownerUsername": "fabriguaglianone",
        "transcript": {"full_text": "Este es el transcript del video"},
        "metadata": {"title": "Título del video"},
    }

    post = ApifyPost(**raw)

    assert post.videoTranscript == "Este es el transcript del video"
    assert post.caption == "Título del video"
