import pathlib

import numpy as np
from sentence_transformers import SentenceTransformer

from api.corpus import company_text
from api.ranking import rank_from_scores

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

EMBEDDING_MODELS = {
    "bge-small": "BAAI/bge-small-en-v1.5",
    "bge-large": "BAAI/bge-large-en-v1.5",
}

# BGE models are asymmetric: passages are embedded plain, but a short
# instruction prefix on the query side measurably improves retrieval.
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class DenseRetriever:
    """Ranks a corpus of companies against a query by embedding cosine similarity."""

    def __init__(self, companies: list[dict], model_key: str = "bge-small"):
        if model_key not in EMBEDDING_MODELS:
            raise ValueError(f"unknown model_key {model_key!r}, expected one of {list(EMBEDDING_MODELS)}")
        self.companies = companies
        self.model_key = model_key
        self.model = SentenceTransformer(EMBEDDING_MODELS[model_key])
        self.embeddings = self._load_or_encode_corpus()

    def _cache_paths(self) -> tuple[pathlib.Path, pathlib.Path]:
        EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
        return (
            EMBEDDINGS_DIR / f"{self.model_key}.npy",
            EMBEDDINGS_DIR / f"{self.model_key}.ids.txt",
        )

    def _load_or_encode_corpus(self) -> np.ndarray:
        vectors_path, ids_path = self._cache_paths()
        current_ids = [str(c["id"]) for c in self.companies]

        if vectors_path.exists() and ids_path.exists():
            cached_ids = ids_path.read_text().splitlines()
            if cached_ids == current_ids:
                return np.load(vectors_path)

        texts = [company_text(c) for c in self.companies]
        embeddings = self.model.encode(
            texts, normalize_embeddings=True, show_progress_bar=True, batch_size=64
        )
        np.save(vectors_path, embeddings)
        ids_path.write_text("\n".join(current_ids))
        return embeddings

    def rank(self, query_text: str, exclude_index: int | None = None) -> list[tuple[int, float]]:
        """Returns (corpus_index, score) pairs sorted by descending relevance."""
        query_vec = self.model.encode(
            QUERY_INSTRUCTION + query_text, normalize_embeddings=True
        )
        scores = self.embeddings @ query_vec
        return rank_from_scores(scores, exclude_index)
