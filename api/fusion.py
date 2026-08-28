from api.lexical import LexicalRetriever
from api.ranking import Retriever
from api.retrieval import DenseRetriever

RRF_K = 60
METHODS = ("dense", "lexical", "fusion")


class FusionRetriever:
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


def build_retriever(companies: list[dict], method: str, model_key: str = "bge-small") -> Retriever:
    if method == "lexical":
        return LexicalRetriever(companies)
    if method == "dense":
        return DenseRetriever(companies, model_key=model_key)
    if method == "fusion":
        dense = DenseRetriever(companies, model_key=model_key)
        lexical = LexicalRetriever(companies)
        return FusionRetriever(dense, lexical)
    raise ValueError(f"unknown method {method!r}, expected one of {METHODS}")
