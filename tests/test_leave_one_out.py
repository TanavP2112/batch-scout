from eval.leave_one_out import RUN_DEPTH, build_qrels, build_run, group_by_subindustry
from tests.conftest import StubRetriever


def _companies():
    return [
        {"id": "c0", "subindustry": "fintech", "long_description": "fintech co zero"},
        {"id": "c1", "subindustry": "fintech", "long_description": "fintech co one"},
        {"id": "c2", "subindustry": "healthtech", "long_description": "health co two"},
        {"id": "c3", "subindustry": "fintech", "one_liner": "fintech co three"},
        {"id": "c4", "subindustry": "devtools"},  # singleton group, no description
    ]


def test_group_by_subindustry_groups_and_preserves_order():
    companies = _companies()

    groups = group_by_subindustry(companies)

    assert groups["fintech"] == [0, 1, 3]
    assert groups["healthtech"] == [2]
    assert groups["devtools"] == [4]


def test_group_by_subindustry_singleton_group():
    companies = _companies()

    groups = group_by_subindustry(companies)

    assert groups["devtools"] == [4]
    assert len(groups["devtools"]) == 1


def test_build_qrels_correct_peer_sets():
    companies = _companies()

    qrels = build_qrels(companies, [0, 2])

    # query index 0 (id c0, fintech) -> peers are c1 and c3 (fintech, not itself)
    assert qrels["c0"] == {"c1": 1, "c3": 1}
    # query index 2 (id c2, healthtech) -> no other healthtech company
    assert qrels["c2"] == {}


def test_build_qrels_singleton_subindustry_yields_empty_dict():
    companies = _companies()

    qrels = build_qrels(companies, [4])

    assert qrels["c4"] == {}


def test_build_qrels_excludes_query_company_itself():
    companies = _companies()

    qrels = build_qrels(companies, [1])

    assert "c1" not in qrels["c1"]
    assert qrels["c1"] == {"c0": 1, "c3": 1}


def test_run_depth_constant_is_100():
    assert RUN_DEPTH == 100


def test_build_run_truncates_to_run_depth():
    # 150 unique companies so truncation isn't masked by companies-list size.
    companies = [{"id": f"c{i}"} for i in range(150)]
    big_ranking = [(i, float(-i)) for i in range(150)]
    retriever = StubRetriever(big_ranking)

    run = build_run(retriever, companies, [0])

    assert len(run["c0"]) == RUN_DEPTH
    assert set(run["c0"]) == {f"c{i}" for i in range(RUN_DEPTH)}


def test_build_run_maps_indices_to_str_ids_with_scores():
    companies = _companies()
    retriever = StubRetriever([(1, 0.9), (2, 0.5), (3, 0.1)])

    run = build_run(retriever, companies, [0])

    assert run["c0"] == {"c1": 0.9, "c2": 0.5, "c3": 0.1}


def test_build_run_passes_exclude_index_through_to_retriever():
    companies = _companies()
    retriever = StubRetriever([(1, 0.9), (2, 0.5)])

    build_run(retriever, companies, [0, 2])

    # Query text should come from companies[qidx]'s description/one_liner.
    called_exclude_indices = [call[1] for call in retriever.calls]
    assert called_exclude_indices == [0, 2]


def test_build_run_uses_query_company_text_as_query():
    companies = _companies()
    retriever = StubRetriever([(1, 0.9)])

    build_run(retriever, companies, [0])

    query_text_used = retriever.calls[0][0]
    assert query_text_used == "fintech co zero"


def test_build_run_falls_back_to_one_liner_for_query_text():
    companies = _companies()
    retriever = StubRetriever([(0, 0.9)])

    build_run(retriever, companies, [3])

    query_text_used = retriever.calls[0][0]
    assert query_text_used == "fintech co three"


def test_build_run_keys_by_query_company_id():
    companies = _companies()
    retriever = StubRetriever([(1, 0.9)])

    run = build_run(retriever, companies, [3])

    assert "c3" in run
    assert run["c3"] == {"c1": 0.9}
