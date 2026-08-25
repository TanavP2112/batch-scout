from api.facets import FACET_NAMES
from api.query import build_query_result


class FakeRetriever:
    """A Retriever stub returning a fixed rank order regardless of query text."""

    def __init__(self, companies: list[dict], order: list[tuple[int, float]]):
        self.companies = companies
        self._order = order

    def rank(self, query_text: str, exclude_index: int | None = None) -> list[tuple[int, float]]:
        return self._order


def facets(customer: str, mechanism: str, wedge: str, business_model: str, problem: str) -> dict:
    return {
        "customer": {"value": customer, "span": "s"},
        "mechanism": {"value": mechanism, "span": "s"},
        "wedge": {"value": wedge, "span": "s"},
        "business_model": {"value": business_model, "span": "s"},
        "problem": {"value": problem, "span": "s"},
    }


def test_companies_are_returned_in_reranked_order_with_alignment_grids():
    companies = [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
    ]
    idea_facets = facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking")
    corpus_facets_by_index = {
        0: facets("enterprise", "SaaS-workflow", "cheaper", "subscription", "expense-tracking"),  # 3 matches
        1: facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking"),  # 4 matches
    }
    # Retriever ranks company 0 first by raw relevance; facet rerank should promote company 1.
    retriever = FakeRetriever(companies, order=[(0, 2.0), (1, 1.0)])

    result = build_query_result(idea_facets, retriever, "some idea text", corpus_facets_by_index)

    ids_in_order = [entry["company"]["id"] for entry in result["companies"]]
    assert ids_in_order == [2, 1]
    assert result["companies"][0]["alignment"]["customer"]["same"] is True


def test_only_top_k_companies_are_returned():
    companies = [{"id": i} for i in range(3)]
    idea_facets = facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking")
    corpus_facets_by_index = {
        i: facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking") for i in range(3)
    }
    retriever = FakeRetriever(companies, order=[(0, 3.0), (1, 2.0), (2, 1.0)])

    result = build_query_result(idea_facets, retriever, "idea", corpus_facets_by_index, top_k=2)

    assert len(result["companies"]) == 2


def test_whitespace_covers_every_facet_over_the_displayed_cohort():
    companies = [{"id": 1}]
    idea_facets = facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking")
    corpus_facets_by_index = {
        0: facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking"),
    }
    retriever = FakeRetriever(companies, order=[(0, 1.0)])

    result = build_query_result(idea_facets, retriever, "idea", corpus_facets_by_index)

    assert set(result["whitespace"]) == set(FACET_NAMES)
    assert "enterprise" in result["whitespace"]["customer"]
    assert "SMB" not in result["whitespace"]["customer"]


def test_problem_whitespace_enum_universe_is_the_full_corpus_not_just_the_displayed_cohort():
    companies = [{"id": 1}, {"id": 2}]
    idea_facets = facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking")
    corpus_facets_by_index = {
        0: facets("SMB", "SaaS-workflow", "cheaper", "subscription", "expense-tracking"),
        # Not displayed (top_k=1), but its problem value still belongs to the corpus-wide enum.
        1: facets("SMB", "SaaS-workflow", "cheaper", "subscription", "payroll-automation"),
    }
    retriever = FakeRetriever(companies, order=[(0, 2.0), (1, 1.0)])

    result = build_query_result(idea_facets, retriever, "idea", corpus_facets_by_index, top_k=1)

    assert "payroll-automation" in result["whitespace"]["problem"]
    assert "expense-tracking" not in result["whitespace"]["problem"]
