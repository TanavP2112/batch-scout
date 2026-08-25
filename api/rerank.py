"""Facet-aware rerank: within the fused top-N, prioritize candidates that
share more idea facets with the query.

Sorts by descending facet_match_count (0-5) with a stable sort, so ties
keep the original retrieval order rather than introducing a tuned weighted
blend — see CONTEXT.md: alignment is a per-facet same/different fact, never
a scalar, and this keeps the rerank in that spirit.

The returned score is *synthetic*, not the original retrieval score: it's
assigned to directly encode the new order (descending by rank position),
because a plain list-reorder that leaves the old scores attached is a
no-op for any consumer that re-sorts by score — ir_measures does exactly
that, ranking purely off the score field and ignoring list/dict order
entirely. The score has to carry the rank, or the rerank doesn't survive
being fed into an IR eval harness.
"""

from api.facets import FACET_NAMES
from api.ranking import Retriever


def facet_match_count(query_facets: dict, candidate_facets: dict) -> int:
    """Counts facets where query and candidate share the same enum value (0-5)."""
    return sum(1 for name in FACET_NAMES if query_facets[name]["value"] == candidate_facets[name]["value"])


def rerank_by_facets(
    ranked: list[tuple[int, float]],
    query_facets: dict,
    facets_by_index: dict[int, dict],
    top_n: int = 50,
) -> list[tuple[int, float]]:
    """Re-sorts the top `top_n` of `ranked` (index, score pairs from a Retriever)
    by descending facet_match_count against `query_facets`, and rewrites the
    score to encode that new order. Ties keep the original order (stable
    sort). Entries beyond `top_n` keep their relative order and always score
    below every reranked entry.
    """
    head, tail = ranked[:top_n], ranked[top_n:]
    reordered = sorted(head, key=lambda pair: -facet_match_count(query_facets, facets_by_index[pair[0]]))

    n_head = len(reordered)
    rescored_head = [(idx, float(n_head - position)) for position, (idx, _) in enumerate(reordered)]
    rescored_tail = [(idx, -float(position + 1)) for position, (idx, _) in enumerate(tail)]
    return rescored_head + rescored_tail


class FacetRerankRetriever:
    """Wraps a Retriever, reranking its top `top_n` by facet match against the
    query's own facets.

    Requires `exclude_index`: in a leave-one-out eval the query *is* corpus
    row `exclude_index`, and its facets are already known from
    data/facets.json — there's no live-query facet extraction here (that's
    build-order step 8's query-time path, not this offline eval).
    """

    def __init__(self, base: Retriever, facets_by_index: dict[int, dict], top_n: int = 50):
        self.companies = base.companies
        self.base = base
        self.facets_by_index = facets_by_index
        self.top_n = top_n

    def rank(self, query_text: str, exclude_index: int | None = None) -> list[tuple[int, float]]:
        if exclude_index is None:
            raise ValueError("FacetRerankRetriever requires exclude_index (the query's own corpus row)")

        ranked = self.base.rank(query_text, exclude_index=exclude_index)
        query_facets = self.facets_by_index[exclude_index]
        return rerank_by_facets(ranked, query_facets, self.facets_by_index, top_n=self.top_n)
