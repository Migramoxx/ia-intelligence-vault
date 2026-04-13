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
        model="claude-3-haiku-20240307",
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    response_text = response.content[0].text.strip()
    
    # Check if the response is a JSON skip status
    try:
        if response_text.startswith('{') and '"status"' in response_text:
            parsed = json.loads(response_text)
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
