from api.whitespace import find_whitespace


def test_enum_value_with_no_occupants_is_whitespace():
    cohort_facets = [{"customer": {"value": "SMB", "span": "s"}}]

    whitespace = find_whitespace(cohort_facets, "customer", ["SMB", "enterprise"])

    assert whitespace == ["enterprise"]


def test_occupied_value_is_not_whitespace():
    cohort_facets = [
        {"customer": {"value": "SMB", "span": "s"}},
        {"customer": {"value": "enterprise", "span": "e"}},
    ]

    whitespace = find_whitespace(cohort_facets, "customer", ["SMB", "enterprise"])

    assert whitespace == []


def test_empty_cohort_makes_every_value_whitespace_in_enum_order():
    enum_values = ["consumer", "SMB", "enterprise", "developer"]

    whitespace = find_whitespace([], "customer", enum_values)

    assert whitespace == enum_values


def test_whitespace_is_computed_on_the_requested_facet_only():
    cohort_facets = [
        {"customer": {"value": "SMB", "span": "s"}, "business_model": {"value": "subscription", "span": "b"}},
    ]

    whitespace = find_whitespace(cohort_facets, "business_model", ["subscription", "take-rate"])

    assert whitespace == ["take-rate"]
