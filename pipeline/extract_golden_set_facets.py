import argparse
import json
import pathlib

from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from dotenv import load_dotenv

from api.anthropic_batch import poll_and_collect as _poll_and_collect
from api.anthropic_batch import submit_batch
from api.facets import build_facet_extraction_params, distinct_facet_values, load_facets
from eval.golden_set import load_golden_set

load_dotenv()

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
FACETS_PATH = DATA_DIR / "facets.json"
GOLDEN_SET_FACETS_PATH = DATA_DIR / "golden_set_facets.json"
BATCH_ID_PATH = DATA_DIR / "golden_set_facets_batch_id.txt"


def problem_enum() -> list[str]:
    """The corpus-derived `problem` enum: every distinct value in the committed facets.json."""
    return distinct_facet_values("problem", load_facets(FACETS_PATH))


def build_idea_request(entry: dict, problem_values: list[str]) -> Request:
    return Request(
        custom_id=entry["id"],
        params=MessageCreateParamsNonStreaming(
            **build_facet_extraction_params(entry["idea_text"], problem_enum=problem_values)
        ),
    )


def submit() -> str:
    golden_set = load_golden_set()
    values = problem_enum()
    requests = [build_idea_request(entry, values) for entry in golden_set]
    return submit_batch(Anthropic(), requests, BATCH_ID_PATH)


def poll_and_collect(batch_id: str, watch: bool = False) -> None:
    collected = _poll_and_collect(Anthropic(), batch_id, watch=watch)
    if collected is None:
        return

    facets, errors = collected
    GOLDEN_SET_FACETS_PATH.write_text(json.dumps(facets, indent=2))
    print(f"wrote {len(facets)} idea facets to {GOLDEN_SET_FACETS_PATH}")
    if errors:
        print(f"{len(errors)} requests did not succeed: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("submit", help="extract facets for all golden-set ideas")

    poll_parser = subparsers.add_parser("poll", help="check batch status; write results once done")
    poll_parser.add_argument("batch_id", nargs="?", default=None)
    poll_parser.add_argument(
        "--watch",
        action="store_true",
        help="keep checking until the batch ends, waiting 30s between checks, instead of a single check",
    )

    args = parser.parse_args()

    if args.command == "submit":
        submit()
    else:
        batch_id = args.batch_id or BATCH_ID_PATH.read_text().strip()
        poll_and_collect(batch_id, watch=args.watch)


if __name__ == "__main__":
    main()
