from types import SimpleNamespace

from api.extract_idea import parse_idea_facets_message


def _message(payload_json, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=payload_json)],
    )


def test_parse_idea_facets_message_returns_parsed_payload():
    message = _message('{"customer": {"value": "SMB", "span": "s"}}')
    assert parse_idea_facets_message(message) == {"customer": {"value": "SMB", "span": "s"}}


def test_parse_idea_facets_message_raises_on_refusal():
    message = _message("{}", stop_reason="refusal")
    try:
        parse_idea_facets_message(message)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "refused" in str(e)
