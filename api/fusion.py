"""Reciprocal Rank Fusion of dense and lexical retrieval.

RRF combines two rankings by rank position rather than raw score, which
sidesteps the fact that BM25 scores and cosine similarities live on
incomparable scales. score(doc) = sum over rankers of 1 / (k + rank), with
the standard k=60 (Cormack et al., 2009).
"""

from api.ranking import Retriever

RRF_K = 60


class FusionRetriever:
    """Ranks a corpus by RRF-fused dense + lexical rank.

    Callers must construct `dense` and `lexical` over the same companies
    list (in the same order) — fusion assumes their corpus indices align.
    """

    def __init__(self, dense: Retriever, lexical: Retriever, k: int = RRF_K):
        self.companies = dense.companies
        self.dense = dense
        self.lexical = lexical
        self.k = k

    def rank(self, query_text: str, exclude_index: int | None = None) -> list[tuple[int, float]]:
        """Returns (corpus_index, rrf_score) pairs sorted by descending relevance."""
        dense_ranked = self.dense.rank(query_text, exclude_index=exclude_index)
        lexical_ranked = self.lexical.rank(query_text, exclude_index=exclude_index)

        scores: dict[int, float] = {}
        for rank, (idx, _) in enumerate(dense_ranked):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (self.k + rank + 1)
        for rank, (idx, _) in enumerate(lexical_ranked):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (self.k + rank + 1)

        order = sorted(scores.items(), key=lambda item: -item[1])
        return [(idx, score) for idx, score in order]
