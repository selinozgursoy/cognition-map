"""
Stage 3 - Window.

Purpose: cut the continuous signal into fixed-length windows. THE WINDOW IS THE
ATOMIC UNIT of the whole product - every point on the map is exactly one window.

Outputs:
  windows : float32 (N, C, T)   raw data per window, kept for the time-linked view
  meta    : DataFrame           one row per window with id, time range, label
Amplitude-based rejection drops obviously corrupted windows here, before they
can become fake clusters.
"""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from .ingest import Recording
from .schema import (
    COL_WINDOW_ID, COL_SUBJECT, COL_SESSION, COL_LABEL, COL_T_START, COL_T_END,
)


def make_windows(rec: Recording, config: dict):
    data = rec.raw.get_data()                  # (C, n_times)
    sfreq = rec.raw.info["sfreq"]
    win = config["window"]
    reject_uv = config["preprocess"].get("reject_amplitude_uv")

    w_samples = int(round(win["seconds"] * sfreq))
    step = max(1, int(round(w_samples * (1.0 - win["overlap"]))))
    drop_unlabeled = win.get("drop_unlabeled", False)
    n_times = data.shape[1]

    windows, rows = [], []
    wid = 0
    for start in range(0, n_times - w_samples + 1, step):
        end = start + w_samples
        chunk = data[:, start:end]             # (C, T)

        # Reject windows with an out-of-range excursion (likely artifact).
        if reject_uv is not None and np.abs(chunk).max() > reject_uv * 1e-6:
            continue

        # Majority label across the window's samples.
        seg_labels = rec.labels[start:end]
        label = Counter(seg_labels).most_common(1)[0][0]

        # On real data, skip windows with no scored stage so gaps don't
        # masquerade as a cluster.
        if drop_unlabeled and label == "unlabeled":
            continue

        windows.append(chunk.astype(np.float32))
        rows.append({
            COL_WINDOW_ID: wid,
            COL_SUBJECT: rec.subject,
            COL_SESSION: rec.session,
            COL_LABEL: str(label),
            COL_T_START: round(start / sfreq, 4),
            COL_T_END: round(end / sfreq, 4),
        })
        wid += 1

    windows = np.stack(windows) if windows else np.empty((0, data.shape[0], w_samples), np.float32)
    meta = pd.DataFrame(rows)
    return windows, meta
