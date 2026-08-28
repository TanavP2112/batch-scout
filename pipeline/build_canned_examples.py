import json
import pathlib

from api.corpus import load_corpus
from api.facets import facets_by_corpus_index, load_facets
from api.fusion import build_retriever
from api.query import build_query_result
from eval.golden_set import GOLDEN_SET_FACETS_PATH, load_golden_set

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
FACETS_PATH = DATA_DIR / "facets.json"
CANNED_EXAMPLES_PATH = DATA_DIR / "canned_examples.json"

CANNED_IDS = [
    "expense-management-smb",
    "ai-scribe-doctors",
    "rural-drone-delivery",
    "defi-onchain-analytics",
    "gig-worker-embedded-insurance",
    "group-trip-planning",
    "biotech-lab-inventory",
    "cloud-cost-monitoring",
]


def select_canned_examples(golden_set: list[dict], ids: list[str]) -> list[dict]:
    by_id = {entry["id"]: entry for entry in golden_set}
    return [by_id[cid] for cid in ids]


def build_canned_examples() -> list[dict]:
    companies = load_corpus()
    retriever = build_retriever(companies, "fusion")
    corpus_facets_by_index = facets_by_corpus_index(companies, load_facets(FACETS_PATH))
    idea_facets_by_id = load_facets(GOLDEN_SET_FACETS_PATH)

    golden_set = load_golden_set()
    examples = select_canned_examples(golden_set, CANNED_IDS)

    return [
        {
            "id": entry["id"],
            "idea_text": entry["idea_text"],
            "result": build_query_result(
                idea_facets_by_id[entry["id"]], retriever, entry["idea_text"], corpus_facets_by_index
            ),
        }
        for entry in examples
    ]


def main() -> None:
    examples = build_canned_examples()
    CANNED_EXAMPLES_PATH.write_text(json.dumps(examples, indent=2))
    print(f"wrote {len(examples)} canned examples to {CANNED_EXAMPLES_PATH}")


if __name__ == "__main__":
    main()
