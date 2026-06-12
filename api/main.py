"""
Cognition Map API.

A thin read layer over the artifacts built by the offline pipeline. Run with:

    uvicorn api.main:app --reload --port 8000

Then open http://localhost:8000/docs for an interactive API explorer.
Point it at a specific run with the COGNITION_RUN env var, otherwise it serves
the most recently built run.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import load_active_run
from .routes import map as map_route
from .routes import window as window_route
from .routes import search as search_route
from .routes import cluster as cluster_route
from .routes import explain as explain_route

app = FastAPI(title="Cognition Map API", version="0.1.0")

# The frontend dev server runs on a different port; allow it to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(map_route.router, prefix="/api")
app.include_router(window_route.router, prefix="/api")
app.include_router(search_route.router, prefix="/api")
app.include_router(cluster_route.router, prefix="/api")
app.include_router(explain_route.router, prefix="/api")


@app.on_event("startup")
def _startup():
    try:
        run = load_active_run()
        print(f"Loaded run {run.manifest['run_hash']} "
              f"({run.manifest['n_windows']} windows, {run.manifest['dataset']})")
    except RuntimeError as e:
        print(f"WARNING: {e}")


@app.get("/api/health")
def health():
    return {"status": "ok"}
