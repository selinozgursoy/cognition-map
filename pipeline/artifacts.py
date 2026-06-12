"""
Artifacts IO + provenance.

Both the pipeline (writer) and the API (reader) go through here, so the on-disk
layout is defined in exactly one place. Each run lives in:

    artifacts/<dataset>/<run_hash>/

where run_hash is derived from the config + a fingerprint of the input data. That
makes every map reproducible and lets you tell whether a cluster moved because of
new data or a new config - the heart of a credible research tool.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import schema

ARTIFACTS_ROOT = Path(__file__).resolve().parent.parent / "artifacts"


def compute_run_hash(config: dict, data_fingerprint: str) -> str:
    payload = json.dumps(config, sort_keys=True) + "|" + data_fingerprint
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def run_dir(dataset: str, run_hash: str) -> Path:
    return ARTIFACTS_ROOT / dataset / run_hash


def write_run(run_path: Path, *, windows, embeddings, coords_df, meta_df,
              index, reducer, manifest: dict) -> None:
    run_path.mkdir(parents=True, exist_ok=True)
    np.save(run_path / schema.WINDOWS_FILE, windows)
    np.save(run_path / schema.EMBEDDINGS_FILE, embeddings)
    coords_df.to_parquet(run_path / schema.COORDS_FILE)
    meta_df.to_parquet(run_path / schema.META_FILE)

    from .index import save_index
    save_index(index, str(run_path / schema.INDEX_FILE))

    from .reduce import save_reducer
    save_reducer(reducer, str(run_path / schema.REDUCER_FILE))

    with open(run_path / schema.MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)


def find_latest_run() -> Path | None:
    """Most recently written run, for the API's default view."""
    if not ARTIFACTS_ROOT.exists():
        return None
    runs = [p for p in ARTIFACTS_ROOT.glob("*/*") if (p / schema.MANIFEST_FILE).exists()]
    if not runs:
        return None
    return max(runs, key=lambda p: (p / schema.MANIFEST_FILE).stat().st_mtime)


class RunArtifacts:
    """Lazy reader the API uses to serve one run."""

    def __init__(self, run_path: Path):
        self.path = run_path
        self.manifest = json.loads((run_path / schema.MANIFEST_FILE).read_text())
        self.coords = pd.read_parquet(run_path / schema.COORDS_FILE)
        self.meta = pd.read_parquet(run_path / schema.META_FILE)
        self._windows = None
        self._embeddings = None
        self._index = None

    @property
    def windows(self) -> np.ndarray:
        if self._windows is None:
            self._windows = np.load(self.path / schema.WINDOWS_FILE)
        return self._windows

    @property
    def embeddings(self) -> np.ndarray:
        if self._embeddings is None:
            self._embeddings = np.load(self.path / schema.EMBEDDINGS_FILE)
        return self._embeddings

    @property
    def index(self):
        if self._index is None:
            from .index import load_index
            self._index = load_index(str(self.path / schema.INDEX_FILE))
        return self._index
