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
    head, tail = ranked[:top_n], ranked[top_n:]
    reordered = sorted(head, key=lambda pair: -facet_match_count(query_facets, facets_by_index[pair[0]]))

    n_head = len(reordered)
    rescored_head = [(idx, float(n_head - position)) for position, (idx, _) in enumerate(reordered)]
    rescored_tail = [(idx, -float(position + 1)) for position, (idx, _) in enumerate(tail)]
    return rescored_head + rescored_tail


class FacetRerankRetriever:
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
