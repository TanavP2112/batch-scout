from api.app import handle_query


class FakeRetriever:
    def __init__(self, companies, order):
        self.companies = companies
        self._order = order

    def rank(self, query_text, exclude_index=None):
        return self._order


def facets(customer="SMB", mechanism="SaaS-workflow", wedge="cheaper", business_model="subscription", problem="p"):
    return {
        "customer": {"value": customer, "span": "s"},
        "mechanism": {"value": mechanism, "span": "s"},
        "wedge": {"value": wedge, "span": "s"},
        "business_model": {"value": business_model, "span": "s"},
        "problem": {"value": problem, "span": "s"},
    }


def test_handle_query_extracts_idea_facets_then_builds_the_response():
    companies = [{"id": 1}]
    corpus_facets_by_index = {0: facets()}
    retriever = FakeRetriever(companies, order=[(0, 1.0)])
    extracted = []

    def fake_extract(idea_text, problem_values):
        extracted.append((idea_text, problem_values))
        return facets()

    result = handle_query(
        "a marketplace for used textbooks",
        retriever=retriever,
        corpus_facets_by_index=corpus_facets_by_index,
        problem_values=["p"],
        extract=fake_extract,
    )

    assert extracted == [("a marketplace for used textbooks", ["p"])]
    assert result["companies"][0]["company"]["id"] == 1
    assert result["companies"][0]["alignment"]["customer"]["same"] is True
