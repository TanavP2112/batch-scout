from typing import Protocol

import numpy as np


class Retriever(Protocol):
    companies: list[dict]

    def rank(self, query_text: str, exclude_index: int | None = None) -> list[tuple[int, float]]: ...


def rank_from_scores(scores: np.ndarray, exclude_index: int | None) -> list[tuple[int, float]]:
    """Returns (corpus_index, score) pairs sorted by descending score.

    `exclude_index` masks one corpus entry out — used by the leave-one-out
    harness so a company never retrieves itself.
    """
    if exclude_index is not None:
        scores = scores.copy()
        scores[exclude_index] = -np.inf
    order = np.argsort(-scores)
    return [(int(i), float(scores[i])) for i in order]
