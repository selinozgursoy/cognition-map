"""
Routes for similarity search (component 3) and novelty.

/api/search   -> given a window, the k most similar windows (searched in the full
                 embedding space, not the 2D map - see pipeline/index.py for why).
/api/novelty  -> the ranked "most unusual moments", so users don't hunt by eye.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline import schema
from pipeline.index import search as faiss_search
from ..deps import get_run

router = APIRouter()


class SearchRequest(BaseModel):
    window_id: int
    k: int = 12


@router.post("/search")
def search(req: SearchRequest):
    run = get_run()
    n = run.manifest["n_windows"]
    if req.window_id < 0 or req.window_id >= n:
        raise HTTPException(404, f"window_id {req.window_id} out of range")

    query = run.embeddings[req.window_id:req.window_id + 1]
    scores, ids = faiss_search(run.index, query, min(req.k + 1, n))

    results = []
    for score, wid in zip(scores[0], ids[0]):
        if wid == req.window_id:                 # skip the query itself
            continue
        row = run.coords[run.coords[schema.COL_WINDOW_ID] == int(wid)].iloc[0]
        results.append({
            "window_id": int(wid),
            "similarity": round(float(score), 4),
            "label": row[schema.COL_LABEL],
        })
        if len(results) >= req.k:
            break
    return {"query": req.window_id, "results": results}


@router.get("/novelty")
def novelty(limit: int = 20):
    run = get_run()
    df = run.coords.sort_values(schema.COL_NOVELTY, ascending=False).head(limit)
    return {
        "most_unusual": [
            {"window_id": int(r[schema.COL_WINDOW_ID]),
             "novelty": round(float(r[schema.COL_NOVELTY]), 4),
             "label": r[schema.COL_LABEL]}
            for _, r in df.iterrows()
        ]
    }
