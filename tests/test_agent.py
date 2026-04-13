from app.models import AgentResponse
from unittest.mock import patch, MagicMock

def test_agent_response_parsing():
    from app.agent import _parse_claude_response
    
    valid_xml = """<response>
  <status>saved</status>
  <reason>Valid technical post</reason>
</response>
<content>
# Technical post Title

Some markdown content here.
</content>"""

    response, content = _parse_claude_response(valid_xml)
    assert response.status == "saved"
    assert response.reason == "Valid technical post"
    assert "# Technical post Title" in content

def test_agent_response_parsing_skipped():
    from app.agent import _parse_claude_response
    
    valid_xml = """<response>
  <status>skipped</status>
  <reason>Not a technical post</reason>
</response>"""

    response, content = _parse_claude_response(valid_xml)
    assert response.status == "skipped"
    assert response.reason == "Not a technical post"
    assert content is None

def test_agent_response_parsing_error():
    from app.agent import _parse_claude_response
    
    invalid_xml = """Invalid response missing XML tags"""

    response, content = _parse_claude_response(invalid_xml)
    assert response.status == "error"
    assert "Failed to parse" in response.reason
    assert content is None
