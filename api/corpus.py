import json
import pathlib

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
SNAPSHOT_PATH = DATA_DIR / "yc-snapshot-2026-08-22.json"


def company_text(company: dict) -> str:
    """The blob embedded for dense retrieval: description, falling back to one-liner."""
    long_description = (company.get("long_description") or "").strip()
    if long_description:
        return long_description
    return (company.get("one_liner") or "").strip()


def load_corpus(path: pathlib.Path | str = SNAPSHOT_PATH) -> list[dict]:
    companies = json.loads(pathlib.Path(path).read_text())
    return [c for c in companies if company_text(c)]
