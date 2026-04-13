import json
from pathlib import Path
from anthropic import Anthropic
from app.config import settings
from app.models import ApifyPost, AgentResponse
import re
from typing import Tuple, Optional

def get_system_prompt() -> str:
    prompt_path = Path("prompts/system_prompt.md")
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""

def process_post(post: ApifyPost) -> Tuple[AgentResponse, Optional[str]]:
    client = Anthropic(api_key=settings.anthropic_api_key)
    system_prompt = get_system_prompt()
    
    user_message = json.dumps(post.model_dump(exclude_none=True), ensure_ascii=False)
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    response_text = response.content[0].text.strip()
    
    # Clean up potential markdown formatting for JSON
    clean_text = response_text
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    
    # Check if the response is a JSON skip/error status
    try:
        if clean_text.startswith('{') and '"status"' in clean_text:
            parsed = json.loads(clean_text)
            return AgentResponse(
                status=parsed.get("status", "skipped"),
                reason=parsed.get("reason", "no_technical_content")
            ), None
    except json.JSONDecodeError:
        pass
    
    # Extract title from Markdown
    title = None
    title_match = re.search(r"##\s+(.+)", response_text)
    if title_match:
        title = title_match.group(1).strip()
        
    return AgentResponse(
        status="saved",
        title=title,
        doc="IA_Intelligence_Vault"
    ), response_text
