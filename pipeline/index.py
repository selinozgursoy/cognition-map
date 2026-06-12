"""
Stage 7 - Index (Search).

Purpose: build a fast nearest-neighbour index over the FULL-DIMENSIONAL embeddings.

Key point: we search in the original embedding space, NOT the 2D map coordinates.
Searching in 2D would return points that look near on screen but are actually
different states (the projection loses information). The map is for the eyes; the
index is for the truth.

We use cosine similarity (L2-normalise, then inner product), which matches the
intuition of "most similar states". FAISS Flat is exact and plenty fast for an MVP;
swap to an approximate index (IVF/HNSW) only when N gets large.
"""
from __future__ import annotations

import numpy as np
import faiss


def _normalize(x: np.ndarray) -> np.ndarray:
    x = np.ascontiguousarray(x.astype(np.float32))
    faiss.normalize_L2(x)
    return x


def build_index(embeddings: np.ndarray):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)             # inner product on normalised vecs = cosine
    index.add(_normalize(embeddings.copy()))
    return index


def save_index(index, path: str) -> None:
    faiss.write_index(index, path)


def load_index(path: str):
    return faiss.read_index(path)


def search(index, query_vecs: np.ndarray, k: int):
    """Return (scores, ids) for each query row. scores are cosine similarity in [-1, 1]."""
    q = _normalize(query_vecs.copy())
    scores, ids = index.search(q, k)
    return scores, ids
