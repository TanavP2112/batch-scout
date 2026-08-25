from eval.golden_set import RUN_DEPTH, build_facet_rerank_run
from tests.conftest import StubRetriever


def _facets(customer="SMB", problem="p", mechanism="m", wedge="w", business_model="b"):
    return {
        "customer": {"value": customer, "span": "s"},
        "problem": {"value": problem, "span": "s"},
        "mechanism": {"value": mechanism, "span": "s"},
        "wedge": {"value": wedge, "span": "s"},
        "business_model": {"value": business_model, "span": "s"},
    }


def test_build_facet_rerank_run_promotes_matching_facets():
    companies = [{"id": "c0"}, {"id": "c1"}]
    golden_set = [{"id": "idea-1", "idea_text": "some idea", "relevant_company_ids": []}]
    idea_facets_by_id = {"idea-1": _facets(customer="SMB")}
    corpus_facets_by_index = {0: _facets(customer="enterprise"), 1: _facets(customer="SMB")}
    # base retrieval ranks index 0 first, but index 1 matches the idea's own facets better
    retriever = StubRetriever([(0, 0.9), (1, 0.5)], companies=companies)

    run = build_facet_rerank_run(retriever, golden_set, idea_facets_by_id, corpus_facets_by_index)

    ranked_ids = list(run["idea-1"])
    assert ranked_ids[0] == "c1"


def test_build_facet_rerank_run_uses_idea_text_as_query():
    companies = [{"id": "c0"}]
    golden_set = [{"id": "idea-1", "idea_text": "founder voice paragraph", "relevant_company_ids": []}]
    idea_facets_by_id = {"idea-1": _facets()}
    corpus_facets_by_index = {0: _facets()}
    retriever = StubRetriever([(0, 0.9)], companies=companies)

    build_facet_rerank_run(retriever, golden_set, idea_facets_by_id, corpus_facets_by_index)

    assert retriever.calls == [("founder voice paragraph", None)]


def test_build_facet_rerank_run_truncates_to_run_depth():
    companies = [{"id": f"c{i}"} for i in range(150)]
    golden_set = [{"id": "idea-1", "idea_text": "x", "relevant_company_ids": []}]
    idea_facets_by_id = {"idea-1": _facets()}
    corpus_facets_by_index = {i: _facets() for i in range(150)}
    retriever = StubRetriever([(i, float(-i)) for i in range(150)], companies=companies)

    run = build_facet_rerank_run(retriever, golden_set, idea_facets_by_id, corpus_facets_by_index)

    assert len(run["idea-1"]) == RUN_DEPTH


def test_build_facet_rerank_run_keys_by_company_id_with_scores():
    companies = [{"id": "c0"}, {"id": "c1"}]
    golden_set = [{"id": "idea-1", "idea_text": "x", "relevant_company_ids": []}]
    idea_facets_by_id = {"idea-1": _facets()}
    corpus_facets_by_index = {0: _facets(), 1: _facets()}
    retriever = StubRetriever([(0, 0.9), (1, 0.5)], companies=companies)

    run = build_facet_rerank_run(retriever, golden_set, idea_facets_by_id, corpus_facets_by_index)

    assert set(run["idea-1"]) == {"c0", "c1"}
