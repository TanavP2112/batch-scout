import json

import pytest

from api.facets import (
    FACET_NAMES,
    distinct_facet_values,
    extraction_schema,
    facets_by_corpus_index,
    load_facets,
    validate_facets,
)


def test_load_facets_reads_json_keyed_by_company_id(tmp_path):
    path = tmp_path / "facets.json"
    path.write_text(json.dumps({"572": {"customer": {"value": "SMB", "span": "s"}}}))

    facets = load_facets(path)

    assert facets == {"572": {"customer": {"value": "SMB", "span": "s"}}}


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


def test_extraction_schema_problem_has_no_enum_by_default():
    schema = extraction_schema()
    value_schema = schema["properties"]["problem"]["properties"]["value"]
    assert "enum" not in value_schema


def test_extraction_schema_problem_enum_when_given():
    schema = extraction_schema(problem_enum=["expense-report-automation", "pet-care"])
    value_schema = schema["properties"]["problem"]["properties"]["value"]
    assert value_schema["enum"] == ["expense-report-automation", "pet-care"]


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


def test_distinct_facet_values_returns_sorted_unique_values():
    facets_by_id = {
        "1": {"problem": {"value": "pet-care", "span": "s"}},
        "2": {"problem": {"value": "expense-tracking", "span": "s"}},
        "3": {"problem": {"value": "pet-care", "span": "s"}},
    }
    assert distinct_facet_values("problem", facets_by_id) == ["expense-tracking", "pet-care"]


def test_facets_by_corpus_index_remaps_by_company_id():
    companies = [{"id": 572}, {"id": 9}]
    facets_by_id = {
        "572": {"customer": {"value": "SMB", "span": "s"}},
        "9": {"customer": {"value": "enterprise", "span": "s"}},
    }
    result = facets_by_corpus_index(companies, facets_by_id)
    assert result == {
        0: {"customer": {"value": "SMB", "span": "s"}},
        1: {"customer": {"value": "enterprise", "span": "s"}},
    }
