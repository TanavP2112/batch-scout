"""FastAPI layer: the query-time path (build-order step 8).

Thin wrapper — all the real logic (ranking, facet-rerank, alignment,
whitespace) lives in api.query.build_query_result, which is pure and
already unit-tested. This module's only job is: extract the live idea's
facets, validate them, hand off to that pure core, and load the retriever
and corpus facets once at process startup rather than per-request.
"""

import pathlib

from anthropic import Anthropic
from fastapi import FastAPI
from pydantic import BaseModel

from api.corpus import load_corpus
from api.extract_idea import extract_idea_facets
from api.facets import load_facets, validate_facets
from api.fusion import build_retriever
from api.query import build_query_result, enum_values_for
from api.ranking import Retriever

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
FACETS_PATH = DATA_DIR / "facets.json"


class QueryRequest(BaseModel):
    idea_text: str


def handle_query(
    idea_text: str,
    retriever: Retriever,
    corpus_facets_by_index: dict[int, dict],
    problem_values: list[str],
    extract=extract_idea_facets,
) -> dict:
    """Extracts the idea's facets, validates them, then delegates to the pure
    ranking/alignment/whitespace core.
    """
    idea_facets = extract(idea_text, problem_values)
    validate_facets(idea_facets)
    return build_query_result(idea_facets, retriever, idea_text, corpus_facets_by_index)


def create_app() -> FastAPI:
    """Loads the corpus, retriever, and committed facets once, then serves /query."""
    app = FastAPI()

    companies = load_corpus()
    retriever = build_retriever(companies, "fusion")
    corpus_facets = load_facets(FACETS_PATH)
    corpus_facets_by_index = {i: corpus_facets[str(c["id"])] for i, c in enumerate(companies)}
    problem_values = enum_values_for("problem", corpus_facets_by_index)
    client = Anthropic()

    @app.post("/query")
    def query(request: QueryRequest) -> dict:
        return handle_query(
            request.idea_text,
            retriever=retriever,
            corpus_facets_by_index=corpus_facets_by_index,
            problem_values=problem_values,
            extract=lambda idea_text, values: extract_idea_facets(idea_text, values, client=client),
        )

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app())
