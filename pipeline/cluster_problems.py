"""Bottom-up clustering of the `problem` facet.

pipeline.extract_facets produces a free-text `problem` label per company but
no enum — a hand-authored problem taxonomy is wrong in ways that surface too
late (see the plan). Instead: embed every label, cluster them, and name each
cluster after its medoid — the member span closest to the cluster's
embedding centroid, computed locally with no API call. Every cluster name
is therefore a real observed span, not a generated one. This script merges
the resulting `problem` enum back into the raw per-facet extractions to
produce the committed data/facets.json.

Usage:
    python -m pipeline.cluster_problems [--k 40]
"""

import argparse
import json
import pathlib
import re

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

from api.retrieval import EMBEDDING_MODELS

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
RAW_FACETS_PATH = DATA_DIR / "facets_raw.json"
FACETS_PATH = DATA_DIR / "facets.json"

SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return SLUG_RE.sub("-", text.lower()).strip("-")


def medoid_index(cluster_embeddings: np.ndarray) -> int:
    """Index (within `cluster_embeddings`) of the point closest to the cluster's centroid."""
    centroid = cluster_embeddings.mean(axis=0)
    distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
    return int(np.argmin(distances))


def name_clusters_by_medoid(spans: list[str], embeddings: np.ndarray, labels, k: int) -> dict[int, str]:
    """Names each cluster after its medoid span, slugified."""
    names: dict[int, str] = {}
    for cluster_idx in range(k):
        member_positions = [i for i, label in enumerate(labels) if int(label) == cluster_idx]
        cluster_embeddings = embeddings[member_positions]
        local_medoid = medoid_index(cluster_embeddings)
        medoid_span = spans[member_positions[local_medoid]]
        names[cluster_idx] = slugify(medoid_span)
    return names


def merge_problem_labels(raw: dict[str, dict], problem_labels: dict[str, str]) -> dict[str, dict]:
    """Rewrites each company's `problem` facet with its cluster-derived value, keeping the original span."""
    return {
        cid: {**entry, "problem": {"value": problem_labels[cid], "span": entry["problem"]["span"]}}
        for cid, entry in raw.items()
    }


def cluster_problems(raw: dict[str, dict], k: int, seed: int) -> dict[str, str]:
    """Returns {company_id: problem_cluster_name}."""
    ids = list(raw.keys())
    # Cluster on the short normalized `value`, not the longer free-text `span` —
    # extract_facets's prompt asks for `value` specifically so it clusters cleanly.
    labels_text = [raw[cid]["problem"]["value"] for cid in ids]

    model = SentenceTransformer(EMBEDDING_MODELS["bge-small"])
    embeddings = model.encode(labels_text, normalize_embeddings=True, show_progress_bar=True, batch_size=64)

    labels = KMeans(n_clusters=k, random_state=seed, n_init="auto").fit_predict(embeddings)

    cluster_names = name_clusters_by_medoid(labels_text, embeddings, labels, k)
    return {cid: cluster_names[int(labels[i])] for i, cid in enumerate(ids)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=40, help="number of problem clusters")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw = json.loads(RAW_FACETS_PATH.read_text())
    print(f"clustering {len(raw)} problem spans into {args.k} clusters")

    problem_labels = cluster_problems(raw, k=args.k, seed=args.seed)
    facets = merge_problem_labels(raw, problem_labels)

    FACETS_PATH.write_text(json.dumps(facets, indent=2))
    print(f"wrote {FACETS_PATH}")


if __name__ == "__main__":
    main()
