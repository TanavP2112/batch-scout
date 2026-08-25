"""Assembles a query response: rank, facet-rerank, then attach an alignment
grid to each displayed company and compute whitespace across the cohort.

Pure over its inputs — no corpus loading, no live extraction call, no
FastAPI. Those are the thin I/O wrappers (api/app.py's query-time extraction,
api/corpus.py's load_corpus) that call this. See CONTEXT.md: alignment is
per-company, whitespace is per-cohort, neither is ever a scalar.
"""

from api.alignment import build_alignment_grid
from api.facets import FACET_ENUMS, FACET_NAMES, distinct_facet_values
from api.ranking import Retriever
from api.rerank import rerank_by_facets
from api.whitespace import find_whitespace


def enum_values_for(facet_name: str, corpus_facets_by_index: dict[int, dict]) -> list[str]:
    """Enum universe for a facet: the hand-authored enum, or (for `problem`,
    which has none) every distinct value observed across the corpus.
    """
    if facet_name in FACET_ENUMS:
        return FACET_ENUMS[facet_name]
    return distinct_facet_values(facet_name, corpus_facets_by_index)


def build_query_result(
    idea_facets: dict,
    retriever: Retriever,
    idea_text: str,
    corpus_facets_by_index: dict[int, dict],
    top_k: int = 12,
    rerank_top_n: int = 50,
) -> dict:
    """Ranks `idea_text`, facet-reranks the top `rerank_top_n`, and returns the
    top `top_k` as {"companies": [{company, alignment, score}], "whitespace": {facet: [values]}}.
    """
    ranked = retriever.rank(idea_text)
    reranked = rerank_by_facets(ranked, idea_facets, corpus_facets_by_index, top_n=rerank_top_n)
    top = reranked[:top_k]

    companies = [
        {
            "company": retriever.companies[idx],
            "alignment": build_alignment_grid(idea_facets, corpus_facets_by_index[idx]),
            "score": score,
        }
        for idx, score in top
    ]

    cohort_facets = [corpus_facets_by_index[idx] for idx, _ in top]
    whitespace = {
        name: find_whitespace(cohort_facets, name, enum_values_for(name, corpus_facets_by_index))
        for name in FACET_NAMES
    }

    return {"companies": companies, "whitespace": whitespace}
