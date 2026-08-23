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
import random
from collections import defaultdict

import ir_measures
from ir_measures import MRR, Recall, nDCG

from api.corpus import load_corpus
from api.retrieval import DenseRetriever

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
    retriever: DenseRetriever, companies: list[dict], query_indices: list[int]
) -> dict[str, dict[str, float]]:
    run: dict[str, dict[str, float]] = {}
    for qidx in query_indices:
        qid = str(companies[qidx]["id"])
        query_text = companies[qidx].get("long_description") or companies[qidx].get("one_liner") or ""
        ranked = retriever.rank(query_text, exclude_index=qidx)[:RUN_DEPTH]
        run[qid] = {str(companies[didx]["id"]): score for didx, score in ranked}
    return run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=300, help="number of sampled queries")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default="bge-small", choices=["bge-small", "bge-large"])
    parser.add_argument("--full", action="store_true", help="use every company as a query")
    args = parser.parse_args()

    companies = load_corpus()
    print(f"corpus: {len(companies)} companies")

    if args.full:
        query_indices = list(range(len(companies)))
    else:
        rng = random.Random(args.seed)
        query_indices = rng.sample(range(len(companies)), min(args.n, len(companies)))
    print(f"queries: {len(query_indices)} (seed={args.seed})")

    retriever = DenseRetriever(companies, model_key=args.model)
    qrels = build_qrels(companies, query_indices)
    run = build_run(retriever, companies, query_indices)

    metrics = [nDCG @ 10, Recall @ 10, MRR]
    results = ir_measures.calc_aggregate(metrics, qrels, run)

    print(f"\nmodel={args.model}  method=leave-one-out (weak labels: same subindustry)")
    for metric, value in results.items():
        print(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    main()
