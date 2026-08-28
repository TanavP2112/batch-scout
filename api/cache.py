import re

_WHITESPACE = re.compile(r"\s+")


def normalize_query(idea_text: str) -> str:
    return _WHITESPACE.sub(" ", idea_text.strip().lower())


class QueryCache:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def get(self, idea_text: str) -> dict | None:
        return self._store.get(normalize_query(idea_text))

    def set(self, idea_text: str, result: dict) -> None:
        self._store[normalize_query(idea_text)] = result
