"""Leave-one-out retrieval eval: the development metric (see plan's Q6 tradeoffs).

Hide a YC company, query with its own description, and check whether its
weak-label peers (other companies in the same `subindustry`) come back.
Free — thousands of labeled queries with zero hand-labeling — but the
weak labels are noisy and the query text is YC's own polished copy rather
than a founder's messy paragraph. This is the harness used for every
ablation; it is not the number quoted in the README (that's the hand-labeled
golden set, a later build-order step).

Usage:
    python -m eval.leave_one_out                       # 300 sampled queries, bge-small
    python -m eval.leave_one_out --n 1000 --model bge-large
    python -m eval.leave_one_out --full                 # every company as a query
"""

import argparse
import pathlib
import random
from collections import defaultdict

import ir_measures
from ir_measures import MRR, Recall, nDCG

from api.corpus import company_text, load_corpus
from api.facets import load_facets
from api.fusion import build_retriever
from api.ranking import Retriever
from api.rerank import FacetRerankRetriever

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
FACETS_PATH = DATA_DIR / "facets.json"

RUN_DEPTH = 100  # candidates kept per query; enough for Recall@10/nDCG@10/MRR


def group_by_subindustry(companies: list[dict]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, company in enumerate(companies):
        groups[company["subindustry"]].append(idx)
    return groups


def build_qrels(companies: list[dict], query_indices: list[int]) -> dict[str, dict[str, int]]:
    """Weak-label ground truth: same-subindustry peers are relevant, everything else isn't."""
    groups = group_by_subindustry(companies)
    qrels: dict[str, dict[str, int]] = {}
    for qidx in query_indices:
        qid = str(companies[qidx]["id"])
        peers = groups[companies[qidx]["subindustry"]]
        qrels[qid] = {str(companies[pidx]["id"]): 1 for pidx in peers if pidx != qidx}
    return qrels


def build_run(
    retriever: Retriever, companies: list[dict], query_indices: list[int]
) -> dict[str, dict[str, float]]:
    run: dict[str, dict[str, float]] = {}
    for qidx in query_indices:
        qid = str(companies[qidx]["id"])
        query_text = company_text(companies[qidx])
        ranked = retriever.rank(query_text, exclude_index=qidx)[:RUN_DEPTH]
        run[qid] = {str(companies[didx]["id"]): score for didx, score in ranked}
    return run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=300, help="number of sampled queries")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default="bge-small", choices=["bge-small", "bge-large"])
    parser.add_argument("--full", action="store_true", help="use every company as a query")
    parser.add_argument(
        "--method",
        default="dense",
        choices=["dense", "lexical", "fusion", "facet-rerank"],
        help="dense-only, BM25-only, RRF fusion, or fusion + facet-aware rerank of the top 50",
    )
    args = parser.parse_args()

    companies = load_corpus()
    print(f"corpus: {len(companies)} companies")

    if args.full:
        query_indices = list(range(len(companies)))
    else:
        rng = random.Random(args.seed)
        query_indices = rng.sample(range(len(companies)), min(args.n, len(companies)))
    print(f"queries: {len(query_indices)} (seed={args.seed})")

    if args.method == "facet-rerank":
        fusion = build_retriever(companies, "fusion", model_key=args.model)
        facets = load_facets(FACETS_PATH)
        facets_by_index = {i: facets[str(c["id"])] for i, c in enumerate(companies)}
        retriever = FacetRerankRetriever(fusion, facets_by_index)
    else:
        retriever = build_retriever(companies, args.method, model_key=args.model)

    qrels = build_qrels(companies, query_indices)
    run = build_run(retriever, companies, query_indices)

    metrics = [nDCG @ 10, Recall @ 10, MRR]
    results = ir_measures.calc_aggregate(metrics, qrels, run)

    print(f"\nmodel={args.model}  method={args.method} (weak labels: same subindustry)")
    for metric, value in results.items():
        print(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    main()
