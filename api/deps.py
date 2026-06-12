"""
Shared API state.

The API is a thin layer over artifacts: it loads ONE run into memory and serves it.
It never touches raw EEG math - that already happened in the offline pipeline.
"""
from __future__ import annotations

import os
from pathlib import Path

from pipeline.artifacts import RunArtifacts, find_latest_run

_active: RunArtifacts | None = None


def load_active_run() -> RunArtifacts:
    """Load the run named by COGNITION_RUN, else the most recent one."""
    global _active
    override = os.environ.get("COGNITION_RUN")
    run_path = Path(override) if override else find_latest_run()
    if run_path is None or not run_path.exists():
        raise RuntimeError(
            "No run found. Build one first: python -m pipeline.run_pipeline "
            "--config configs/default.yaml"
        )
    _active = RunArtifacts(run_path)
    return _active


def get_run() -> RunArtifacts:
    if _active is None:
        return load_active_run()
    return _active
