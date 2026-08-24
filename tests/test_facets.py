import pytest

from api.facets import FACET_NAMES, extraction_schema, validate_facets


def test_extraction_schema_requires_all_five_facets():
    schema = extraction_schema()
    assert set(schema["required"]) == set(FACET_NAMES)
    assert set(schema["properties"]) == set(FACET_NAMES)


def test_extraction_schema_controlled_facets_have_enum():
    schema = extraction_schema()
    for name in ("customer", "mechanism", "wedge", "business_model"):
        value_schema = schema["properties"][name]["properties"]["value"]
        assert "enum" in value_schema
        assert len(value_schema["enum"]) > 0


def test_extraction_schema_problem_has_no_enum():
    schema = extraction_schema()
    value_schema = schema["properties"]["problem"]["properties"]["value"]
    assert "enum" not in value_schema


def test_extraction_schema_facet_requires_value_and_span():
    schema = extraction_schema()
    for name in FACET_NAMES:
        assert schema["properties"][name]["required"] == ["value", "span"]
        assert schema["properties"][name]["additionalProperties"] is False


def _valid_facets():
    return {
        "customer": {"value": "SMB", "span": "small businesses"},
        "problem": {"value": "expense-report-automation", "span": "manual expense reports"},
        "mechanism": {"value": "SaaS-workflow", "span": "web dashboard"},
        "wedge": {"value": "faster", "span": "same-day approval"},
        "business_model": {"value": "subscription", "span": "monthly seat pricing"},
    }


def test_validate_facets_accepts_valid_facets():
    validate_facets(_valid_facets())  # no exception


def test_validate_facets_rejects_unknown_enum_value():
    facets = _valid_facets()
    facets["customer"]["value"] = "not-a-real-value"
    with pytest.raises(ValueError, match="customer"):
        validate_facets(facets)


def test_validate_facets_rejects_missing_facet():
    facets = _valid_facets()
    del facets["wedge"]
    with pytest.raises(ValueError, match="wedge"):
        validate_facets(facets)


def test_validate_facets_does_not_require_problem_enum_membership():
    facets = _valid_facets()
    facets["problem"]["value"] = "anything-goes-here"
    validate_facets(facets)  # no exception — problem has no fixed enum
