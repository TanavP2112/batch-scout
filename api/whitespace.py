"""Whitespace: enum values unoccupied across a retrieved cohort of companies.

See CONTEXT.md — computed by counting occupants per value, never generated
by the model. This module only counts; prose around a finding is written
elsewhere.
"""


def find_whitespace(cohort_facets: list[dict], facet_name: str, enum_values: list[str]) -> list[str]:
    occupied = {facets[facet_name]["value"] for facets in cohort_facets}
    return [value for value in enum_values if value not in occupied]
