from types import SimpleNamespace

from api.extract_idea import build_idea_request_kwargs, parse_idea_facets_message


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


def test_build_idea_request_kwargs_embeds_idea_text_and_problem_enum():
    kwargs = build_idea_request_kwargs("a marketplace for used textbooks", problem_values=["book-resale"])

    assert kwargs["messages"] == [{"role": "user", "content": "a marketplace for used textbooks"}]
    schema = kwargs["output_config"]["format"]["schema"]
    assert schema["properties"]["problem"]["properties"]["value"]["enum"] == ["book-resale"]
