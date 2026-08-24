"""Golden-set retrieval eval: hand-labeled founder-voice ideas.

The reporting metric quoted in the README (unlike eval.leave_one_out, the
development metric used for ablations) — see the plan's Q6 tradeoff table.
Small (30 ideas, wide confidence intervals) and single-labeler, and query
text is deliberately messy founder-voice paragraphs rather than YC's own
polished marketing copy, closing the distribution-mismatch gap
leave-one-out has. An idea with zero labeled `relevant_company_ids` is a
legitimate label — it means this corpus has no real prior art for that idea,
not a labeling gap.

Usage:
    python -m eval.golden_set                       # 30 ideas, bge-small
    python -m eval.golden_set --method fusion
"""

import argparse
import json
import pathlib

import ir_measures
from ir_measures import MRR, Recall, nDCG

from api.corpus import load_corpus
from api.fusion import build_retriever
from api.ranking import Retriever

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
GOLDEN_SET_PATH = DATA_DIR / "golden_set.json"

RUN_DEPTH = 100  # candidates kept per query; enough for Recall@10/nDCG@10/MRR


def load_golden_set(path: pathlib.Path | str = GOLDEN_SET_PATH) -> list[dict]:
    return json.loads(pathlib.Path(path).read_text())


def build_qrels(golden_set: list[dict]) -> dict[str, dict[str, int]]:
    return {
        entry["id"]: {str(cid): 1 for cid in entry["relevant_company_ids"]}
        for entry in golden_set
    }


def build_run(retriever: Retriever, golden_set: list[dict]) -> dict[str, dict[str, float]]:
    run: dict[str, dict[str, float]] = {}
    for entry in golden_set:
        ranked = retriever.rank(entry["idea_text"])[:RUN_DEPTH]
        run[entry["id"]] = {str(retriever.companies[idx]["id"]): score for idx, score in ranked}
    return run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="bge-small", choices=["bge-small", "bge-large"])
    parser.add_argument(
        "--method",
        default="fusion",
        choices=["dense", "lexical", "fusion"],
        help="dense-only, BM25-only, or RRF fusion of both",
    )
    args = parser.parse_args()

    companies = load_corpus()
    golden_set = load_golden_set()
    print(f"corpus: {len(companies)} companies")
    print(f"golden set: {len(golden_set)} ideas")

    retriever = build_retriever(companies, args.method, model_key=args.model)

    qrels = build_qrels(golden_set)
    run = build_run(retriever, golden_set)

    metrics = [nDCG @ 10, Recall @ 10, MRR]
    results = ir_measures.calc_aggregate(metrics, qrels, run)

    print(f"\nmodel={args.model}  method={args.method} (golden set, hand-labeled)")
    for metric, value in results.items():
        print(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    main()
