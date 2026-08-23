import pytest

from api.fusion import RRF_K, FusionRetriever
from tests.conftest import StubRetriever


def _companies():
    return [{"id": 0}, {"id": 1}, {"id": 2}]


def test_rrf_k_constant_is_60():
    assert RRF_K == 60


def test_fusion_retriever_stores_companies_from_dense():
    companies = _companies()
    dense = StubRetriever([(0, 0.9), (1, 0.5), (2, 0.1)], companies=companies)
    lexical = StubRetriever([(1, 5.0), (0, 3.0), (2, 1.0)], companies=companies)

    fusion = FusionRetriever(dense, lexical)

    assert fusion.companies == dense.companies


def test_fusion_retriever_combines_ranks_with_k_1():
    # dense ranking: 0 (rank0), 1 (rank1), 2 (rank2)
    # lexical ranking: 1 (rank0), 0 (rank1), 2 (rank2)
    companies = _companies()
    dense = StubRetriever([(0, 0.9), (1, 0.5), (2, 0.1)], companies=companies)
    lexical = StubRetriever([(1, 5.0), (0, 3.0), (2, 1.0)], companies=companies)

    fusion = FusionRetriever(dense, lexical, k=1)
    result = fusion.rank("some query")

    # contribution = 1/(k + rank + 1) = 1/(1+rank+1) = 1/(rank+2)
    # index 0: dense rank0 -> 1/2 = 0.5 ; lexical rank1 -> 1/3 = 0.3333...
    # index 1: dense rank1 -> 1/3 = 0.3333...; lexical rank0 -> 1/2 = 0.5
    # index 2: dense rank2 -> 1/4 = 0.25; lexical rank2 -> 1/4 = 0.25
    expected = {
        0: 0.5 + (1.0 / 3.0),
        1: (1.0 / 3.0) + 0.5,
        2: 0.25 + 0.25,
    }

    scores = {idx: score for idx, score in result}
    assert scores[0] == pytest.approx(expected[0])
    assert scores[1] == pytest.approx(expected[1])
    assert scores[2] == pytest.approx(expected[2])

    # 0 and 1 tie, both above 2.
    indices = [idx for idx, _ in result]
    assert indices.index(2) > indices.index(0)
    assert indices.index(2) > indices.index(1)


def test_fusion_retriever_index_present_in_only_one_ranking_contributes_zero():
    companies = [{"id": 0}, {"id": 1}, {"id": 2}]
    # dense only returns 0 and 1; lexical only returns 1 and 2.
    dense = StubRetriever([(0, 0.9), (1, 0.5)], companies=companies)
    lexical = StubRetriever([(1, 5.0), (2, 1.0)], companies=companies)

    fusion = FusionRetriever(dense, lexical, k=1)
    result = fusion.rank("some query")
    scores = {idx: score for idx, score in result}

    # index 0: only dense, rank0 -> 1/(1+0+1) = 0.5
    assert scores[0] == pytest.approx(0.5)
    # index 2: only lexical, rank1 -> 1/(1+1+1) = 1/3
    assert scores[2] == pytest.approx(1.0 / 3.0)
    # index 1: both, dense rank1 -> 1/3, lexical rank0 -> 1/2
    assert scores[1] == pytest.approx((1.0 / 3.0) + 0.5)

    # all three indices appear since each appeared in at least one ranking.
    assert set(scores.keys()) == {0, 1, 2}

    # ordering: 1 (0.833) > 0 (0.5) > 2 (0.333)
    indices = [idx for idx, _ in result]
    assert indices.index(1) < indices.index(0) < indices.index(2)


def test_fusion_retriever_default_k_is_rrf_k():
    companies = _companies()
    dense = StubRetriever([(0, 0.9), (1, 0.5), (2, 0.1)], companies=companies)
    lexical = StubRetriever([(0, 3.0), (1, 5.0), (2, 1.0)], companies=companies)

    fusion = FusionRetriever(dense, lexical)

    assert fusion.k == RRF_K


def test_fusion_retriever_passes_query_and_exclude_index_to_both_retrievers():
    companies = _companies()
    dense = StubRetriever([(0, 0.9), (1, 0.5), (2, 0.1)], companies=companies)
    lexical = StubRetriever([(0, 3.0), (1, 5.0), (2, 1.0)], companies=companies)

    fusion = FusionRetriever(dense, lexical, k=1)
    fusion.rank("my query text", exclude_index=2)

    assert dense.calls == [("my query text", 2)]
    assert lexical.calls == [("my query text", 2)]
