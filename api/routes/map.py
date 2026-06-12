"""
Routes that feed the brain-state map canvas (component 1).

/api/manifest -> provenance + label list (so the UI knows what it's showing)
/api/map      -> every window's coordinates, label, and novelty (the point cloud)
"""
from __future__ import annotations

from fastapi import APIRouter

from pipeline import schema
from ..deps import get_run

router = APIRouter()


@router.get("/manifest")
def manifest():
    run = get_run()
    m = run.manifest
    return {
        "run_hash": m["run_hash"],
        "dataset": m["dataset"],
        "n_windows": m["n_windows"],
        "labels": m["labels"],
        "channel_names": m["channel_names"],
        "sfreq": m["sfreq"],
        "created_utc": m["created_utc"],
    }


@router.get("/map")
def get_map():
    """Return points for the canvas. Kept lean - just what's needed to draw + colour.

    Points come back ordered by window_id, which is also time order, so the frontend
    can connect consecutive points into the trajectory view for free.
    """
    run = get_run()
    df = run.coords.sort_values(schema.COL_WINDOW_ID)
    cols = [schema.COL_WINDOW_ID, schema.COL_X, schema.COL_Y, schema.COL_LABEL, schema.COL_NOVELTY]
    if schema.COL_Z in df.columns:
        cols.insert(3, schema.COL_Z)
    return {
        "points": df[cols].to_dict(orient="records"),
        "labels": run.manifest["labels"],
    }
