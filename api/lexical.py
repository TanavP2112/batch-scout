import re

import numpy as np
from rank_bm25 import BM25Okapi

from api.corpus import company_text
from api.ranking import rank_from_scores

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class LexicalRetriever:
    """Ranks a corpus of companies against a query by BM25 score."""

    def __init__(self, companies: list[dict]):
        self.companies = companies
        self.corpus_tokens = [tokenize(company_text(c)) for c in companies]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def rank(self, query_text: str, exclude_index: int | None = None) -> list[tuple[int, float]]:
        """Returns (corpus_index, score) pairs sorted by descending relevance."""
        scores = np.asarray(self.bm25.get_scores(tokenize(query_text)))
        return rank_from_scores(scores, exclude_index)
