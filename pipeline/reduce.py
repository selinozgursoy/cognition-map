"""
Stage 5 - Reduce (Map).

Purpose: project the high-dimensional embeddings down to 2D (or 3D) so they can be
drawn. UMAP preserves local neighbourhoods, which is what makes "similar states
live near each other" actually true on screen.

Important: we SAVE the fitted reducer. That lets you project a brand-new window
into the same map later (e.g. live data) without recomputing everything.
"""
from __future__ import annotations

import numpy as np
import joblib


def reduce(embeddings: np.ndarray, config: dict):
    """embeddings: (N, D) -> (coords (N, n_components), fitted_reducer)."""
    cfg = config["reduce"]
    method = cfg["method"]
    n = cfg["n_components"]

    if method == "umap":
        import umap
        u = cfg["umap"]
        reducer = umap.UMAP(
            n_components=n,
            n_neighbors=u["n_neighbors"],
            min_dist=u["min_dist"],
            metric=u["metric"],
            random_state=u["seed"],
        )
        coords = reducer.fit_transform(embeddings)
    elif method == "pca":
        from sklearn.decomposition import PCA
        reducer = PCA(n_components=n)
        coords = reducer.fit_transform(embeddings)
    elif method == "tsne":
        from sklearn.manifold import TSNE
        reducer = TSNE(n_components=n, init="pca")
        coords = reducer.fit_transform(embeddings)   # note: t-SNE can't project new points
    else:
        raise ValueError(f"Unknown reduce method: {method}")

    return np.asarray(coords, dtype=np.float32), reducer


def save_reducer(reducer, path: str) -> None:
    try:
        joblib.dump(reducer, path)
    except Exception:
        pass   # t-SNE and some objects don't pickle cleanly; not fatal for the MVP
