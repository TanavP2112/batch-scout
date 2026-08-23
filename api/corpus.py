"""Loads the pinned YC snapshot into the shape retrieval needs.

A company with neither a long_description nor a one_liner has nothing to
embed and is dropped — 57 of 6,189 in the current snapshot.
"""

import json
import pathlib

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
SNAPSHOT_PATH = DATA_DIR / "yc-snapshot-2026-08-22.json"


def company_text(company: dict) -> str:
    """The blob embedded for dense retrieval: description, falling back to one-liner."""
    return (company.get("long_description") or company.get("one_liner") or "").strip()


def load_corpus(path: pathlib.Path = SNAPSHOT_PATH) -> list[dict]:
    companies = json.loads(path.read_text())
    return [c for c in companies if company_text(c)]
