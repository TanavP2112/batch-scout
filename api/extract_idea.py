import json

from anthropic import Anthropic

from api.facets import extraction_schema
from pipeline.extract_facets import MODEL, SYSTEM_PROMPT


def build_idea_request_kwargs(idea_text: str, problem_values: list[str]) -> dict:
    return {
        "model": MODEL,
        "max_tokens": 2048,
        "thinking": {"type": "adaptive"},
        "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": idea_text}],
        "output_config": {"format": {"type": "json_schema", "schema": extraction_schema(problem_enum=problem_values)}},
    }


def parse_idea_facets_message(message) -> dict:
    """Raises ValueError if the model refused or returned no text block."""
    if message.stop_reason == "refusal":
        raise ValueError("model refused to classify this idea")

    text_block = next((b for b in message.content if b.type == "text"), None)
    if text_block is None:
        raise ValueError("no text block in response")

    return json.loads(text_block.text)


def extract_idea_facets(idea_text: str, problem_values: list[str], client: Anthropic | None = None) -> dict:
    client = client or Anthropic()
    message = client.messages.create(**build_idea_request_kwargs(idea_text, problem_values))
    return parse_idea_facets_message(message)
