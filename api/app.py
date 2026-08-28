import pathlib

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from api.cache import QueryCache
from api.corpus import load_corpus
from api.extract_idea import extract_idea_facets
from api.facets import facets_by_corpus_index, load_facets, validate_facets
from api.fusion import build_retriever
from api.query import build_query_result, enum_values_for
from api.ranking import Retriever
from api.ratelimit import RateLimiter

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
FACETS_PATH = DATA_DIR / "facets.json"

PER_IP_PER_HOUR = 20
DAILY_CAP = 200
DEMO_LIMIT_DETAIL = "demo limit reached — please try again later"


class QueryRequest(BaseModel):
    idea_text: str


def handle_query(
    idea_text: str,
    retriever: Retriever,
    corpus_facets_by_index: dict[int, dict],
    problem_values: list[str],
    extract=extract_idea_facets,
    cache: QueryCache | None = None,
) -> dict:
    """Extracts the idea's facets, validates them, then delegates to the pure
    ranking/alignment/whitespace core. A hit on `cache` skips extraction and
    ranking entirely — repeat pokes at the same idea cost nothing.
    """
    if cache is not None:
        cached = cache.get(idea_text)
        if cached is not None:
            return cached

    idea_facets = extract(idea_text, problem_values)
    validate_facets(idea_facets)
    result = build_query_result(idea_facets, retriever, idea_text, corpus_facets_by_index)

    if cache is not None:
        cache.set(idea_text, result)
    return result


def check_rate_limit(limiter: RateLimiter, ip: str) -> None:
    """Raises HTTPException(429) if `ip` is over either window (per-IP or the
    shared daily cap) — the plan's "degrade to a message, not an error" means
    a friendly, non-5xx response, not disguising a rejection as a 200.
    """
    if not limiter.allow(ip):
        raise HTTPException(status_code=429, detail=DEMO_LIMIT_DETAIL)


def create_app() -> FastAPI:
    """Loads the corpus, retriever, and committed facets once, then serves /query."""
    app = FastAPI()

    companies = load_corpus()
    retriever = build_retriever(companies, "fusion")
    corpus_facets_by_index = facets_by_corpus_index(companies, load_facets(FACETS_PATH))
    problem_values = enum_values_for("problem", corpus_facets_by_index)
    client = Anthropic()
    cache = QueryCache()
    limiter = RateLimiter(per_ip_per_hour=PER_IP_PER_HOUR, daily_cap=DAILY_CAP)

    @app.post("/query")
    def query(request: QueryRequest, http_request: Request) -> dict:
        ip = http_request.client.host if http_request.client else "unknown"
        check_rate_limit(limiter, ip)

        return handle_query(
            request.idea_text,
            retriever=retriever,
            corpus_facets_by_index=corpus_facets_by_index,
            problem_values=problem_values,
            extract=lambda idea_text, values: extract_idea_facets(idea_text, values, client=client),
            cache=cache,
        )

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app())
