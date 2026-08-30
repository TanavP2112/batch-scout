import json
import pathlib

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You are classifying a startup into five facets, used to compare it against other startups.

- customer: who the primary buyer/user is.
- problem: the core problem being solved, as a short (3-6 word) normalized label — this will later be clustered against thousands of other companies' labels, so phrase it as a generic problem category (e.g. "expense report automation", not "helping accountants at mid-size firms file expenses faster").
- mechanism: how the product is delivered/works.
- wedge: what makes this startup's entry angle work — why now, why them.
- business_model: how the company makes money.

For each facet, also return a short (<=12 word) free-text span quoting or closely paraphrasing the source text that supports the classification. Base every judgment only on the given text — do not invent facts."""

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


def build_facet_extraction_params(text: str, problem_enum: list[str] | None = None) -> dict:
    """The shared Claude request shape for classifying one text into the five
    facets — used identically for corpus companies, golden-set ideas, and a
    live typed idea, so the same classifier decides every side of every
    alignment-grid comparison. Pass `problem_enum` (the corpus-derived
    enum) when the result needs to be comparable to already-extracted
    facets; omit it for the initial corpus pass, before that enum exists.
    """
    return {
        "model": MODEL,
        "max_tokens": 2048,
        "thinking": {"type": "adaptive"},
        "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": text}],
        "output_config": {"format": {"type": "json_schema", "schema": extraction_schema(problem_enum)}},
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
