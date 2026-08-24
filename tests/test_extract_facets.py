from api.facets import FACET_NAMES
from pipeline.extract_facets import build_request


def _company(company_id=42, name="Acme", long_description="Widgets for widgets."):
    return {"id": company_id, "name": name, "long_description": long_description}


def test_build_request_uses_company_id_as_custom_id():
    request = build_request(_company(company_id=7))
    assert request["custom_id"] == "7"


def test_build_request_includes_name_and_text_in_message():
    request = build_request(_company(name="Acme", long_description="Widgets for widgets."))
    content = request["params"]["messages"][0]["content"]
    assert "Acme" in content
    assert "Widgets for widgets." in content


def test_build_request_uses_structured_output_schema():
    request = build_request(_company())
    schema = request["params"]["output_config"]["format"]["schema"]
    assert set(schema["required"]) == set(FACET_NAMES)
