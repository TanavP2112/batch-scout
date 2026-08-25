import pytest

from api.rerank import FacetRerankRetriever, facet_match_count, rerank_by_facets
from tests.conftest import StubRetriever


def _facets(customer="SMB", problem="p", mechanism="m", wedge="w", business_model="b"):
    return {
        "customer": {"value": customer, "span": "s"},
        "problem": {"value": problem, "span": "s"},
        "mechanism": {"value": mechanism, "span": "s"},
        "wedge": {"value": wedge, "span": "s"},
        "business_model": {"value": business_model, "span": "s"},
    }


def test_facet_match_count_all_same_is_five():
    assert facet_match_count(_facets(), _facets()) == 5


def test_facet_match_count_counts_only_matching_facets():
    query = _facets(customer="SMB", mechanism="SaaS-workflow")
    candidate = _facets(customer="SMB", mechanism="marketplace")
    assert facet_match_count(query, candidate) == 4  # customer, problem, wedge, business_model match; mechanism doesn't


def test_facet_match_count_none_same_is_zero():
    query = _facets(customer="SMB", problem="p1", mechanism="m1", wedge="w1", business_model="b1")
    candidate = _facets(customer="enterprise", problem="p2", mechanism="m2", wedge="w2", business_model="b2")
    assert facet_match_count(query, candidate) == 0


def test_rerank_by_facets_promotes_higher_match_count_within_top_n():
    query_facets = _facets(customer="SMB")
    facets_by_index = {
        0: _facets(customer="enterprise"),  # 4 matches
        1: _facets(customer="SMB"),  # 5 matches
        2: _facets(customer="enterprise"),  # 4 matches
    }
    ranked = [(0, 0.9), (1, 0.5), (2, 0.1)]  # index 1 ranked last by base retrieval

    result = rerank_by_facets(ranked, query_facets, facets_by_index, top_n=3)

    assert result[0][0] == 1  # best facet match promoted to first


def test_rerank_by_facets_ties_keep_original_order():
    query_facets = _facets(customer="SMB")
    facets_by_index = {
        0: _facets(customer="enterprise"),
        1: _facets(customer="enterprise"),
    }
    ranked = [(0, 0.9), (1, 0.5)]

    result = rerank_by_facets(ranked, query_facets, facets_by_index, top_n=2)

    assert [idx for idx, _ in result] == [0, 1]  # equal match count (4 each) -> original order preserved


def test_rerank_by_facets_leaves_tail_beyond_top_n_untouched():
    query_facets = _facets(customer="SMB")
    facets_by_index = {
        0: _facets(customer="enterprise"),
        1: _facets(customer="SMB"),  # would win if reranked, but it's past top_n
    }
    ranked = [(0, 0.9), (1, 0.5)]

    result = rerank_by_facets(ranked, query_facets, facets_by_index, top_n=1)

    assert [idx for idx, _ in result] == [0, 1]  # only the first element was eligible for reordering


def test_rerank_by_facets_scores_encode_the_new_order():
    # A plain list-reorder that leaves the old scores attached doesn't survive
    # any consumer that re-sorts by score (e.g. ir_measures does exactly this,
    # ignoring list/dict order entirely) — the score itself must carry the
    # final rank, or the "rerank" is silently a no-op for such consumers.
    query_facets = _facets(customer="SMB")
    facets_by_index = {
        0: _facets(customer="enterprise"),  # was ranked first, matches less
        1: _facets(customer="SMB"),  # was ranked last, matches better -> promoted
    }
    ranked = [(0, 0.9), (1, 0.1)]

    result = rerank_by_facets(ranked, query_facets, facets_by_index, top_n=2)

    scores = dict(result)
    assert scores[1] > scores[0]  # promoted item's score reflects its new, better rank


def test_rerank_by_facets_tail_scores_stay_below_every_head_score():
    query_facets = _facets(customer="SMB")
    facets_by_index = {0: _facets(customer="SMB"), 1: _facets(customer="SMB"), 2: _facets(customer="SMB")}
    ranked = [(0, 100.0), (1, 50.0), (2, 0.001)]  # index 2's original score would otherwise leak above nothing here

    result = rerank_by_facets(ranked, query_facets, facets_by_index, top_n=2)

    scores = dict(result)
    head_scores = [scores[0], scores[1]]
    assert scores[2] < min(head_scores)  # tail (untouched by reordering) always sorts below the reranked head


def test_facet_rerank_retriever_requires_exclude_index():
    base = StubRetriever([(0, 0.9)], companies=[{"id": "c0"}])
    retriever = FacetRerankRetriever(base, facets_by_index={0: _facets()})

    with pytest.raises(ValueError, match="exclude_index"):
        retriever.rank("some query")


def test_facet_rerank_retriever_uses_exclude_index_row_as_query_facets():
    companies = [{"id": "c0"}, {"id": "c1"}, {"id": "c2"}]
    facets_by_index = {
        0: _facets(customer="SMB"),  # this is the query (exclude_index=0)
        1: _facets(customer="enterprise"),
        2: _facets(customer="SMB"),
    }
    base = StubRetriever([(1, 0.9), (2, 0.5)], companies=companies)
    retriever = FacetRerankRetriever(base, facets_by_index, top_n=2)

    result = retriever.rank("query text", exclude_index=0)

    assert result[0][0] == 2  # matches query's own facets (SMB), promoted over index 1
    assert base.calls == [("query text", 0)]


def test_facet_rerank_retriever_exposes_companies_from_base():
    companies = [{"id": "c0"}]
    base = StubRetriever([], companies=companies)
    retriever = FacetRerankRetriever(base, facets_by_index={})
    assert retriever.companies == companies
