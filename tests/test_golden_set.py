from eval.golden_set import RUN_DEPTH, build_qrels, build_run
from tests.conftest import StubRetriever


def test_build_qrels_maps_query_id_to_relevant_company_ids():
    golden_set = [{"id": "expense-tracking", "idea_text": "...", "relevant_company_ids": [572, 1050]}]

    qrels = build_qrels(golden_set)

    assert qrels == {"expense-tracking": {"572": 1, "1050": 1}}


def test_build_qrels_empty_relevant_ids_is_a_legitimate_empty_dict():
    golden_set = [{"id": "no-prior-art", "idea_text": "...", "relevant_company_ids": []}]

    qrels = build_qrels(golden_set)

    assert qrels == {"no-prior-art": {}}


def test_build_run_maps_corpus_indices_to_company_ids_with_scores():
    companies = [{"id": "c0"}, {"id": "c1"}, {"id": "c2"}]
    golden_set = [{"id": "idea-1", "idea_text": "some idea text", "relevant_company_ids": []}]
    retriever = StubRetriever([(1, 0.9), (2, 0.5)], companies=companies)

    run = build_run(retriever, golden_set)

    assert run["idea-1"] == {"c1": 0.9, "c2": 0.5}


def test_build_run_passes_idea_text_as_query():
    companies = [{"id": "c0"}]
    golden_set = [{"id": "idea-1", "idea_text": "founder voice paragraph", "relevant_company_ids": []}]
    retriever = StubRetriever([(0, 0.9)], companies=companies)

    build_run(retriever, golden_set)

    assert retriever.calls == [("founder voice paragraph", None)]


def test_build_run_truncates_to_run_depth():
    companies = [{"id": f"c{i}"} for i in range(150)]
    golden_set = [{"id": "idea-1", "idea_text": "x", "relevant_company_ids": []}]
    retriever = StubRetriever([(i, float(-i)) for i in range(150)], companies=companies)

    run = build_run(retriever, golden_set)

    assert len(run["idea-1"]) == RUN_DEPTH
