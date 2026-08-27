from api.app import DEMO_LIMIT_MESSAGE, check_rate_limit, handle_query
from api.cache import QueryCache
from api.ratelimit import RateLimiter


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


def test_handle_query_reuses_a_cached_result_without_calling_extract_again():
    companies = [{"id": 1}]
    corpus_facets_by_index = {0: facets()}
    retriever = FakeRetriever(companies, order=[(0, 1.0)])
    cache = QueryCache()
    calls = []

    def fake_extract(idea_text, problem_values):
        calls.append(idea_text)
        return facets()

    kwargs = dict(
        retriever=retriever,
        corpus_facets_by_index=corpus_facets_by_index,
        problem_values=["p"],
        extract=fake_extract,
        cache=cache,
    )
    first = handle_query("a marketplace for used textbooks", **kwargs)
    second = handle_query("A Marketplace for Used Textbooks", **kwargs)

    assert calls == ["a marketplace for used textbooks"]
    assert second == first


def test_check_rate_limit_allows_under_the_cap():
    limiter = RateLimiter(per_ip_per_hour=1, daily_cap=100)
    assert check_rate_limit(limiter, "1.2.3.4") is None


def test_check_rate_limit_degrades_to_the_demo_message_once_over_the_cap():
    limiter = RateLimiter(per_ip_per_hour=1, daily_cap=100)
    check_rate_limit(limiter, "1.2.3.4")
    assert check_rate_limit(limiter, "1.2.3.4") == DEMO_LIMIT_MESSAGE
