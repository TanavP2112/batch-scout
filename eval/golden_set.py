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
from api.facets import load_facets
from api.fusion import build_retriever
from api.ranking import Retriever
from api.rerank import rerank_by_facets

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
GOLDEN_SET_PATH = DATA_DIR / "golden_set.json"
FACETS_PATH = DATA_DIR / "facets.json"
GOLDEN_SET_FACETS_PATH = DATA_DIR / "golden_set_facets.json"

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


def build_facet_rerank_run(
    retriever: Retriever,
    golden_set: list[dict],
    idea_facets_by_id: dict[str, dict],
    corpus_facets_by_index: dict[int, dict],
) -> dict[str, dict[str, float]]:
    """Like build_run, but reranks each idea's top-50 by facet match first.

    Doesn't reuse api.rerank.FacetRerankRetriever — that wrapper gets the
    query's facets via `exclude_index` (leave-one-out's query *is* a corpus
    row). A golden-set idea isn't a corpus row; its facets come from
    data/golden_set_facets.json, keyed by the idea's own id, which this
    loop already has — no need to smuggle it through the Retriever protocol.
    """
    run: dict[str, dict[str, float]] = {}
    for entry in golden_set:
        ranked = retriever.rank(entry["idea_text"])
        reranked = rerank_by_facets(ranked, idea_facets_by_id[entry["id"]], corpus_facets_by_index)
        run[entry["id"]] = {str(retriever.companies[idx]["id"]): score for idx, score in reranked[:RUN_DEPTH]}
    return run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="bge-small", choices=["bge-small", "bge-large"])
    parser.add_argument(
        "--method",
        default="fusion",
        choices=["dense", "lexical", "fusion", "facet-rerank"],
        help="dense-only, BM25-only, RRF fusion, or fusion + facet-aware rerank of the top 50",
    )
    args = parser.parse_args()

    companies = load_corpus()
    golden_set = load_golden_set()
    print(f"corpus: {len(companies)} companies")
    print(f"golden set: {len(golden_set)} ideas")

    qrels = build_qrels(golden_set)

    if args.method == "facet-rerank":
        fusion = build_retriever(companies, "fusion", model_key=args.model)
        corpus_facets = load_facets(FACETS_PATH)
        corpus_facets_by_index = {i: corpus_facets[str(c["id"])] for i, c in enumerate(companies)}
        idea_facets_by_id = load_facets(GOLDEN_SET_FACETS_PATH)
        run = build_facet_rerank_run(fusion, golden_set, idea_facets_by_id, corpus_facets_by_index)
    else:
        retriever = build_retriever(companies, args.method, model_key=args.model)
        run = build_run(retriever, golden_set)

    metrics = [nDCG @ 10, Recall @ 10, MRR]
    results = ir_measures.calc_aggregate(metrics, qrels, run)

    print(f"\nmodel={args.model}  method={args.method} (golden set, hand-labeled)")
    for metric, value in results.items():
        print(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    main()
