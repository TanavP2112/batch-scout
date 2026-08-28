import argparse
import json
import pathlib

from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from dotenv import load_dotenv

from api.anthropic_batch import poll_and_collect as _poll_and_collect
from api.anthropic_batch import submit_batch
from api.corpus import company_text, load_corpus
from api.facets import extraction_schema

load_dotenv()

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
RAW_FACETS_PATH = DATA_DIR / "facets_raw.json"
BATCH_ID_PATH = DATA_DIR / "facets_batch_id.txt"

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You are classifying a startup into five facets, used to compare it against other startups.

- customer: who the primary buyer/user is.
- problem: the core problem being solved, as a short (3-6 word) normalized label — this will later be clustered against thousands of other companies' labels, so phrase it as a generic problem category (e.g. "expense report automation", not "helping accountants at mid-size firms file expenses faster").
- mechanism: how the product is delivered/works.
- wedge: what makes this startup's entry angle work — why now, why them.
- business_model: how the company makes money.

For each facet, also return a short (<=12 word) free-text span quoting or closely paraphrasing the source text that supports the classification. Base every judgment only on the given text — do not invent facts."""


def build_request(company: dict) -> Request:
    text = f"{company['name']}: {company_text(company)}"
    return Request(
        custom_id=str(company["id"]),
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": text}],
            output_config={"format": {"type": "json_schema", "schema": extraction_schema()}},
        ),
    )


def submit(companies: list[dict]) -> str:
    requests = [build_request(c) for c in companies]
    return submit_batch(Anthropic(), requests, BATCH_ID_PATH)


def poll_and_collect(batch_id: str, watch: bool = False) -> None:
    collected = _poll_and_collect(Anthropic(), batch_id, watch=watch)
    if collected is None:
        return

    facets, errors = collected
    RAW_FACETS_PATH.write_text(json.dumps(facets, indent=2))
    print(f"wrote {len(facets)} extractions to {RAW_FACETS_PATH}")
    if errors:
        print(f"{len(errors)} requests did not succeed: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_parser = subparsers.add_parser("submit", help="create and submit a batch")
    submit_parser.add_argument("--n", type=int, default=None, help="limit to first N companies (testing)")

    poll_parser = subparsers.add_parser("poll", help="check batch status; write results once done")
    poll_parser.add_argument("batch_id", nargs="?", default=None, help="defaults to the last-submitted batch id")
    poll_parser.add_argument(
        "--watch",
        action="store_true",
        help="keep checking until the batch ends, waiting 30s between checks, instead of a single check",
    )

    args = parser.parse_args()

    if args.command == "submit":
        companies = load_corpus()
        if args.n:
            companies = companies[: args.n]
        submit(companies)
    else:
        batch_id = args.batch_id or BATCH_ID_PATH.read_text().strip()
        poll_and_collect(batch_id, watch=args.watch)


if __name__ == "__main__":
    main()
