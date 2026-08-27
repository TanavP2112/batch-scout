"""Normalized-hash cache for query-time facet extraction + retrieval.

Per the plan: repeat pokes at the same idea (or a trivially-reworded one)
cost nothing — no repeated Claude call, no repeated ranking pass. Keyed on
normalized text rather than the raw string so "A Marketplace for Used
Textbooks" and "a marketplace  for used textbooks" hit the same entry.
"""

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_query(idea_text: str) -> str:
    return _WHITESPACE.sub(" ", idea_text.strip().lower())


class QueryCache:
    """In-memory cache from normalized idea text to a full query result.

    Process-local and unbounded — sized for a single-container demo, not a
    production deployment; see CLAUDE.md's architecture note on why this
    ships as one container.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}

    def get(self, idea_text: str) -> dict | None:
        return self._store.get(normalize_query(idea_text))

    def set(self, idea_text: str, result: dict) -> None:
        self._store[normalize_query(idea_text)] = result
