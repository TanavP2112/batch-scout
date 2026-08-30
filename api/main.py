"""ASGI entrypoint: `uvicorn api.main:app`.

Kept separate from api.app so importing api.app (e.g. from tests, for its
pure functions) never triggers create_app()'s real side effects — loading
the corpus, building the retriever, and constructing a live Anthropic
client. Only this module, actually run as a server, pays that cost.
"""

from api.app import create_app

app = create_app()
