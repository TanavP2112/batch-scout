"""Idea facet schema: the five bilateral facets shared by ideas and companies.

Each facet pairs a controlled enum (deterministic alignment-grid comparison,
whitespace counting) with a free-text span (readable UI). See CONTEXT.md for
the idea-facet / cohort-signal distinction.

`problem` has no hand-authored enum — its values are derived bottom-up by
clustering free-text spans (pipeline/cluster_problems.py) rather than
guessed upfront, per the plan's rationale that a hand-authored taxonomy is
wrong in ways that surface too late.
"""

CUSTOMER = [
    "consumer",
    "prosumer",
    "SMB",
    "mid-market",
    "enterprise",
    "developer",
    "regulated-institution",
    "public-sector",
    "marketplace-both-sides",
]

MECHANISM = [
    "marketplace",
    "SaaS-workflow",
    "AI-agent/copilot",
    "infrastructure/API",
    "hardware",
    "embedded-fintech",
    "data/analytics",
    "services-augmented",
    "protocol/crypto",
]

WEDGE = [
    "cheaper",
    "faster",
    "new-user-segment",
    "unbundling-incumbent",
    "regulatory-arbitrage",
    "novel-capability",
    "distribution-hack",
]

BUSINESS_MODEL = [
    "subscription",
    "usage-based",
    "take-rate",
    "ads",
    "licensing",
    "services",
    "hardware-margin",
]

# Controlled-enum facets extracted directly. `problem` is handled separately
# (see module docstring) and is deliberately absent from this dict.
FACET_ENUMS = {
    "customer": CUSTOMER,
    "mechanism": MECHANISM,
    "wedge": WEDGE,
    "business_model": BUSINESS_MODEL,
}

# All five facet names, in the order they're displayed.
FACET_NAMES = ["customer", "problem", "mechanism", "wedge", "business_model"]


def _facet_property(enum_values: list[str] | None) -> dict:
    value_schema = {"type": "string", "enum": enum_values} if enum_values else {"type": "string"}
    return {
        "type": "object",
        "properties": {"value": value_schema, "span": {"type": "string"}},
        "required": ["value", "span"],
        "additionalProperties": False,
    }


def extraction_schema() -> dict:
    """JSON schema for one company/idea's facet extraction (output_config.format).

    `problem.value` has no enum yet — it's filled in by the clustering pass.
    Requiring it as a string here still forces the model to produce *some*
    normalized short label, which seeds the clustering step.
    """
    return {
        "type": "object",
        "properties": {
            **{name: _facet_property(enum) for name, enum in FACET_ENUMS.items()},
            "problem": _facet_property(None),
        },
        "required": FACET_NAMES,
        "additionalProperties": False,
    }


def validate_facets(facets: dict) -> None:
    """Raises ValueError if `facets` doesn't match the extraction contract.

    Structured outputs already enforce enum membership at generation time;
    this is for validating facets loaded back from disk (e.g. after the
    clustering merge rewrites `problem`), where that guarantee no longer holds.
    """
    missing = [name for name in FACET_NAMES if name not in facets]
    if missing:
        raise ValueError(f"missing facets: {missing}")

    for name, enum_values in FACET_ENUMS.items():
        value = facets[name]["value"]
        if value not in enum_values:
            raise ValueError(f"{name}={value!r} not in {enum_values}")
