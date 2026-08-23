"""Shared test doubles and assertion helpers for the retrieval test suite."""


class StubRetriever:
    """Duck-typed fake retriever: returns a fixed ranking, records each call's args."""

    def __init__(self, ranking, companies=None):
        self.companies = companies
        self._ranking = ranking
        self.calls = []

    def rank(self, query_text, exclude_index=None):
        self.calls.append((query_text, exclude_index))
        return list(self._ranking)


def assert_excluded_ranked_last(indices, excluded, others):
    """Per the exclude_index contract: excluded must never outrank another index."""
    if excluded in indices:
        pos_excluded = indices.index(excluded)
        for other in others:
            assert indices.index(other) < pos_excluded
    else:
        assert excluded not in indices
