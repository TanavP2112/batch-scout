import json

from anthropic import Anthropic

from api.facets import build_facet_extraction_params


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
    message = client.messages.create(**build_facet_extraction_params(idea_text, problem_enum=problem_values))
    return parse_idea_facets_message(message)
