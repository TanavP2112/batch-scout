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
from api.facets import build_facet_extraction_params

load_dotenv()

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
RAW_FACETS_PATH = DATA_DIR / "facets_raw.json"
BATCH_ID_PATH = DATA_DIR / "facets_batch_id.txt"


def build_request(company: dict) -> Request:
    text = f"{company['name']}: {company_text(company)}"
    return Request(
        custom_id=str(company["id"]),
        params=MessageCreateParamsNonStreaming(**build_facet_extraction_params(text)),
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
