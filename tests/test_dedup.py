def test_is_duplicate():
    from services.dedup import is_duplicate
    
    doc_content = "Here is some content\nhttps://www.instagram.com/p/12345/\nAnd another url https://www.instagram.com/p/67890/\n"
    
    assert is_duplicate("https://www.instagram.com/p/12345/", doc_content) is True
    assert is_duplicate("https://www.instagram.com/p/67890/", doc_content) is True
    assert is_duplicate("https://www.instagram.com/p/abcde/", doc_content) is False

def test_is_duplicate_empty_doc():
    from services.dedup import is_duplicate
    
    doc_content = ""
    assert is_duplicate("https://www.instagram.com/p/12345/", doc_content) is False
