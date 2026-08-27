from api.cache import QueryCache, normalize_query


def test_normalize_query_lowercases_and_collapses_whitespace():
    assert normalize_query("  A Marketplace   for USED\ttextbooks  ") == "a marketplace for used textbooks"


def test_cache_returns_none_for_unseen_query():
    cache = QueryCache()
    assert cache.get("a new idea") is None


def test_cache_returns_stored_result_for_the_same_query():
    cache = QueryCache()
    cache.set("a marketplace for used textbooks", {"companies": []})

    assert cache.get("a marketplace for used textbooks") == {"companies": []}


def test_cache_hits_on_near_identical_query_text():
    cache = QueryCache()
    cache.set("A Marketplace for Used Textbooks", {"companies": []})

    assert cache.get("  a marketplace   for used textbooks") == {"companies": []}


def test_cache_misses_on_a_genuinely_different_query():
    cache = QueryCache()
    cache.set("a marketplace for used textbooks", {"companies": []})

    assert cache.get("a payroll app for restaurants") is None
