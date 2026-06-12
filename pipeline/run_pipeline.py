"""
Pipeline orchestrator.

Runs every stage in order and writes one reproducible run to disk:

    ingest -> preprocess -> window -> embed -> reduce -> novelty -> index -> write

Usage:
    python -m pipeline.run_pipeline --config configs/default.yaml

The run is fully described by the config file plus a fingerprint of the input data,
hashed into run_hash. Re-running with the same config + data is a no-op-equivalent
(same hash, same folder).
"""
from __future__ import annotations

import argparse
import hashlib
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yaml

from . import schema
from .artifacts import compute_run_hash, run_dir, write_run
from .ingest import load_recording
from .preprocess import preprocess
from .window import make_windows
from .embed import embed
from .reduce import reduce
from .novelty import novelty_scores
from .index import build_index


def _data_fingerprint(rec) -> str:
    """Cheap, stable fingerprint of the input signal for the run hash."""
    data = rec.raw.get_data()
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(data[:, ::97]).tobytes())   # subsample for speed
    h.update(str(rec.raw.info["sfreq"]).encode())
    return h.hexdigest()[:16]


def run(config: dict) -> str:
    print(f"[1/7] ingest      ({config['dataset']})")
    rec = load_recording(config)

    print("[2/7] preprocess  (filter + notch)")
    rec = preprocess(rec, config)

    print("[3/7] window")
    windows, meta = make_windows(rec, config)
    sfreq = float(rec.raw.info["sfreq"])
    print(f"        -> {len(windows)} windows, shape {windows.shape}")

    print(f"[4/7] embed       (backend={config['embed']['backend']})")
    embeddings = embed(windows, config, sfreq)
    print(f"        -> embeddings {embeddings.shape}")

    print(f"[5/7] reduce      ({config['reduce']['method']} -> {config['reduce']['n_components']}D)")
    coords, reducer = reduce(embeddings, config)

    print("[6/7] novelty")
    nov = novelty_scores(embeddings, config["novelty"]["k"])

    print("[7/7] index")
    index = build_index(embeddings)

    # Assemble coords table (what the canvas reads).
    coords_df = meta[[schema.COL_WINDOW_ID, schema.COL_LABEL]].copy()
    coords_df[schema.COL_X] = coords[:, 0]
    coords_df[schema.COL_Y] = coords[:, 1]
    if coords.shape[1] >= 3:
        coords_df[schema.COL_Z] = coords[:, 2]
    coords_df[schema.COL_NOVELTY] = nov

    data_fp = _data_fingerprint(rec)
    run_hash = compute_run_hash(config, data_fp)
    run_path = run_dir(config["dataset"], run_hash)

    manifest = {
        "run_hash": run_hash,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": config["dataset"],
        "config": config,
        "data_fingerprint": data_fp,
        "n_windows": int(len(windows)),
        "embedding_dim": int(embeddings.shape[1]),
        "window_shape": list(windows.shape[1:]),
        "sfreq": sfreq,
        "channel_names": rec.raw.info["ch_names"],
        "labels": sorted(meta[schema.COL_LABEL].unique().tolist()),
        "versions": {"python": platform.python_version()},
    }

    write_run(run_path, windows=windows, embeddings=embeddings, coords_df=coords_df,
              meta_df=meta, index=index, reducer=reducer, manifest=manifest)
    print(f"\nDone. Run written to: {run_path}")
    print(f"run_hash = {run_hash}")
    return str(run_path)


def main():
    ap = argparse.ArgumentParser(description="Build a Cognition Map run.")
    ap.add_argument("--config", default="configs/default.yaml")
    args = ap.parse_args()
    with open(args.config) as f:
        config = yaml.safe_load(f)
    run(config)


if __name__ == "__main__":
    main()
