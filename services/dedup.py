def is_duplicate(url: str, doc_content: str) -> bool:
    """Verifica si la URL ya existe en el contenido del documento."""
    return url in doc_content
