"""
Route for the model explainability layer (component 5).

Two explanations, both grounded in the SAME features that built the map (so the
explanation is honest, not a separate post-hoc story):

/api/explain/similarity -> "why are these two windows similar?" For the query and a
        neighbour, report which bands match most closely (small difference = the
        thing driving the match) and which differ. This answers the user's natural
        next question after every search.

/api/explain/cluster   -> "what defines this region?" The averaged per-channel band
        profile of a selection - a physiological fingerprint. The per-channel numbers
        are exactly what you'd feed an MNE topomap to render a scalp map.
"""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline import schema
from pipeline.embed import relative_band_powers
from ..deps import get_run

router = APIRouter()


class SimilarityRequest(BaseModel):
    window_id: int
    neighbor_id: int


class ClusterRequest(BaseModel):
    window_ids: list[int]


@router.post("/explain/similarity")
def explain_similarity(req: SimilarityRequest):
    run = get_run()
    n = run.manifest["n_windows"]
    if not (0 <= req.window_id < n and 0 <= req.neighbor_id < n):
        raise HTTPException(404, "window_id out of range")

    sfreq = run.manifest["sfreq"]
    bands, a = relative_band_powers(run.windows[req.window_id], sfreq)
    _, b = relative_band_powers(run.windows[req.neighbor_id], sfreq)
    a, b = a.mean(axis=0), b.mean(axis=0)        # average across channels

    diffs = np.abs(a - b)
    contributions = []
    for band, av, bv, d in zip(bands, a, b, diffs):
        contributions.append({
            "band": band,
            "query": round(float(av), 3),
            "neighbor": round(float(bv), 3),
            "abs_diff": round(float(d), 3),
        })
    contributions.sort(key=lambda c: c["abs_diff"])
    return {
        "drives_match": [c["band"] for c in contributions[:2]],   # most alike
        "drives_difference": [c["band"] for c in contributions[-2:][::-1]],
        "bands": contributions,
    }


@router.post("/explain/cluster")
def explain_cluster(req: ClusterRequest):
    run = get_run()
    n = run.manifest["n_windows"]
    ids = [w for w in req.window_ids if 0 <= w < n]
    if not ids:
        raise HTTPException(400, "No valid window_ids.")

    sfreq = run.manifest["sfreq"]
    ch_names = run.manifest["channel_names"]
    stacked = []
    for wid in ids:
        bands, rel = relative_band_powers(run.windows[wid], sfreq)   # (C, n_bands)
        stacked.append(rel)
    mean_rel = np.mean(stacked, axis=0)            # (C, n_bands)

    return {
        "n_windows": len(ids),
        "bands": bands,
        "channel_profile": {                       # per-channel per-band -> feeds a topomap
            ch: [round(float(v), 3) for v in mean_rel[i]]
            for i, ch in enumerate(ch_names)
        },
        "overall_profile": {
            b: round(float(mean_rel[:, j].mean()), 3) for j, b in enumerate(bands)
        },
    }
