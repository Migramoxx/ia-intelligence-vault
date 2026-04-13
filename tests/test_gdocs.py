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

    def test_partial_url_does_not_match(self):
        """Una URL parcial no debe matchear la URL completa."""
        url = "https://instagram.com/p/ABC123/"
        doc_content = "https://instagram.com/p/ABC"  # sin el /123/ final
        assert not is_duplicate(url, doc_content)


class TestIsDuplicate:
    def test_url_in_doc_content(self):
        url = "https://instagram.com/p/ABC123/"
        doc_content = f"## Claude Computer Use\n**Fuente:** @user\n{url}\n"
        assert is_duplicate(url, doc_content)

    def test_exact_url_match(self):
        url = "https://www.instagram.com/p/C_EXACT_MATCH/"
        assert is_duplicate(url, f"Procesado el 2026-04-10: {url}")

    def test_url_in_middle_of_content(self):
        url = "https://www.instagram.com/p/C_MIDDLE_001/"
        doc_content = (
            "---\n## Herramienta X\n\n"
            f"| Fuente | @cuenta |\n---\n{url}\n---\n"
            "## Otra herramienta\n---\n"
        )
        assert is_duplicate(url, doc_content)
