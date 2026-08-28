import json
import pathlib

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


def extraction_schema(problem_enum: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": {
            **{name: _facet_property(enum) for name, enum in FACET_ENUMS.items()},
            "problem": _facet_property(problem_enum),
        },
        "required": FACET_NAMES,
        "additionalProperties": False,
    }


def validate_facets(facets: dict) -> None:
    missing = [name for name in FACET_NAMES if name not in facets]
    if missing:
        raise ValueError(f"missing facets: {missing}")

    for name, enum_values in FACET_ENUMS.items():
        value = facets[name]["value"]
        if value not in enum_values:
            raise ValueError(f"{name}={value!r} not in {enum_values}")


def load_facets(path: pathlib.Path | str) -> dict[str, dict]:
    """Loads a facets.json-shaped file: {company_id: {facet_name: {value, span}}}."""
    return json.loads(pathlib.Path(path).read_text())


def distinct_facet_values(facet_name: str, facets_by_id: dict[str, dict]) -> list[str]:
    return sorted({entry[facet_name]["value"] for entry in facets_by_id.values()})


def facets_by_corpus_index(companies: list[dict], facets_by_id: dict[str, dict]) -> dict[int, dict]:
    return {i: facets_by_id[str(c["id"])] for i, c in enumerate(companies)}
