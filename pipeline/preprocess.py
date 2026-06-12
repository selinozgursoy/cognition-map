"""
Stage 2 - Preprocess.

Purpose: clean the signal so the embeddings reflect brain activity, not blinks,
drift, or mains hum. Embeddings are only as meaningful as the signal going in -
garbage windows create fake clusters that look like discoveries.

MNE does all of this natively, which is exactly why it's the backbone here.
"""
from __future__ import annotations

import mne

from .ingest import Recording


def preprocess(rec: Recording, config: dict) -> Recording:
    cfg = config["preprocess"]
    raw = rec.raw.copy()

    # Band-pass: drop slow drifts (< l_freq) and high-frequency noise (> h_freq).
    raw.filter(
        l_freq=cfg["l_freq"],
        h_freq=cfg["h_freq"],
        verbose="ERROR",
    )

    # Notch: remove mains hum (50 Hz in much of the world, 60 Hz in N. America).
    if cfg.get("notch"):
        raw.notch_filter(freqs=[cfg["notch"]], verbose="ERROR")

    return Recording(raw=raw, labels=rec.labels, subject=rec.subject, session=rec.session)
