"""
Stage 6 - Novelty ("find weird events").

Purpose: score how unusual each window is, so the app can surface a ranked list of
the strangest moments instead of making the user hunt for them by eye.

Method: a window's novelty = its mean distance to its k nearest neighbours in the
embedding space. Windows in dense regions (common states) score low; windows in
sparse regions (rare / anomalous states) score high. Cheap, because the index for
similarity search already gives us neighbours.

Scores are normalised to 0..1 for easy colour-mapping on the canvas.
"""
from __future__ import annotations

import numpy as np
from sklearn.neighbors import NearestNeighbors


def novelty_scores(embeddings: np.ndarray, k: int) -> np.ndarray:
    n = len(embeddings)
    if n <= 1:
        return np.zeros(n, dtype=np.float32)
    k = min(k, n - 1)
    nn = NearestNeighbors(n_neighbors=k + 1, metric="cosine").fit(embeddings)
    dist, _ = nn.kneighbors(embeddings)        # first column is self (distance 0)
    raw = dist[:, 1:].mean(axis=1)
    lo, hi = raw.min(), raw.max()
    norm = (raw - lo) / (hi - lo + 1e-12)
    return norm.astype(np.float32)
