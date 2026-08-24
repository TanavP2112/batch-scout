"""LLM-as-judge: Claude scores retrieved (idea, company) pairs for relevance.

Coverage check per the plan: catches false negatives that eval.leave_one_out's
weak subindustry labels and eval.golden_set's small hand-labeled set both
miss, by judging every pair actually retrieved rather than relying on
pre-existing labels. Not independent of the system under test — it favors
fluent matches and would be circular if retrieval were ever tuned against
it, so it's a coverage check, not a reporting metric.

Batch submit/poll/watch lifecycle lives in api.anthropic_batch — this module
supplies only the judging-specific request shape.

Usage:
    python -m eval.llm_judge submit    # judge eval.golden_set's fusion top-10 run
    python -m eval.llm_judge poll [--watch] [batch_id]
"""

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
from api.fusion import build_retriever
from eval.golden_set import build_run, load_golden_set

load_dotenv()

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
JUDGMENTS_PATH = DATA_DIR / "llm_judgments.json"
JUDGE_BATCH_ID_PATH = DATA_DIR / "llm_judge_batch_id.txt"

MODEL = "claude-sonnet-5"
JUDGED_DEPTH = 10  # judge each idea's top-10 retrieved companies

JUDGE_SYSTEM_PROMPT = (
    "You are judging whether a company is a relevant prior-art match for a "
    "founder's startup idea — i.e. would a founder researching this idea "
    "want to know this company exists? Judge on problem/customer/mechanism "
    "similarity, not surface wording. Be a skeptical judge: a company in a "
    "loosely related space is not automatically relevant."
)


def judge_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "relevant": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["relevant", "reason"],
        "additionalProperties": False,
    }


def judge_custom_id(query_id: str, company_id) -> str:
    return f"{query_id}::{company_id}"


def build_judge_request(query_id: str, idea_text: str, company: dict) -> Request:
    prompt = f"Founder's idea: {idea_text}\n\nCompany: {company['name']}: {company_text(company)}"
    return Request(
        custom_id=judge_custom_id(query_id, company["id"]),
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=1024,
            thinking={"type": "adaptive"},
            system=[{"type": "text", "text": JUDGE_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": judge_schema()}},
        ),
    )


def build_judge_pairs(run: dict[str, dict[str, float]], depth: int = JUDGED_DEPTH) -> list[tuple[str, str]]:
    """Returns (query_id, company_id) pairs to judge: each query's top `depth` retrieved companies.

    Relies on eval.golden_set.build_run's ordering contract — its dict is
    built directly from a Retriever's already rank-sorted output, and dicts
    preserve insertion order, so `scored`'s iteration order already is rank
    order. Re-sorting here would be redundant.
    """
    pairs = []
    for query_id, scored in run.items():
        pairs.extend((query_id, company_id) for company_id in list(scored)[:depth])
    return pairs


def coverage_report(judgments: dict[str, dict], qrels: dict[str, dict[str, int]]) -> dict[str, dict]:
    """Per query: judged-relevant count, and judged-relevant pairs absent from qrels
    (candidate false negatives — the whole point of running a judge alongside weak labels).
    """
    report: dict[str, dict] = {}
    for custom_id, judgment in judgments.items():
        query_id, company_id = custom_id.split("::", 1)
        report.setdefault(query_id, {"judged_relevant": 0, "judged_relevant_not_in_qrels": []})
        if judgment["relevant"]:
            report[query_id]["judged_relevant"] += 1
            if company_id not in qrels.get(query_id, {}):
                report[query_id]["judged_relevant_not_in_qrels"].append(company_id)
    return report


def submit() -> str:
    companies = load_corpus()
    golden_set = load_golden_set()
    companies_by_id = {str(c["id"]): c for c in companies}

    fusion = build_retriever(companies, "fusion")
    run = build_run(fusion, golden_set)

    idea_text_by_id = {entry["id"]: entry["idea_text"] for entry in golden_set}
    pairs = build_judge_pairs(run)

    requests = [
        build_judge_request(query_id, idea_text_by_id[query_id], companies_by_id[company_id])
        for query_id, company_id in pairs
    ]
    return submit_batch(Anthropic(), requests, JUDGE_BATCH_ID_PATH)


def poll_and_collect(batch_id: str, watch: bool = False) -> None:
    collected = _poll_and_collect(Anthropic(), batch_id, watch=watch)
    if collected is None:
        return

    judgments, errors = collected
    JUDGMENTS_PATH.write_text(json.dumps(judgments, indent=2))
    print(f"wrote {len(judgments)} judgments to {JUDGMENTS_PATH}")
    if errors:
        print(f"{len(errors)} requests did not succeed: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("submit", help="judge the fusion retriever's golden-set top-10")

    poll_parser = subparsers.add_parser("poll", help="check batch status; write judgments once done")
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
        batch_id = args.batch_id or JUDGE_BATCH_ID_PATH.read_text().strip()
        poll_and_collect(batch_id, watch=args.watch)


if __name__ == "__main__":
    main()
