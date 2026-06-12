"""
Route that feeds the time-linked view (component 2).

/api/window/{id} -> the raw multichannel EEG for that window + a spectrogram +
                    where it sits in the recording. This is the trust-builder:
                    clicking a dot and seeing real brainwaves makes the abstract
                    map believable.

Raw traces are downsampled for transport (the screen can't show every sample anyway).
"""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException
from scipy import signal as sp_signal

from pipeline import schema
from ..deps import get_run

router = APIRouter()

MAX_POINTS_PER_TRACE = 256   # plenty for a preview; keeps payloads small


@router.get("/window/{window_id}")
def get_window(window_id: int):
    run = get_run()
    if window_id < 0 or window_id >= run.manifest["n_windows"]:
        raise HTTPException(404, f"window_id {window_id} out of range")

    win = run.windows[window_id]                       # (C, T) in volts
    sfreq = run.manifest["sfreq"]
    ch_names = run.manifest["channel_names"]

    # Downsample each channel for the preview trace.
    C, T = win.shape
    step = max(1, T // MAX_POINTS_PER_TRACE)
    traces = (win[:, ::step] * 1e6).round(2).tolist()  # to microvolts
    t_axis = (np.arange(0, T, step) / sfreq).round(4).tolist()

    # Spectrogram of the channel with the most power (most informative preview).
    ch = int(np.argmax(win.var(axis=1)))
    f, t, Sxx = sp_signal.spectrogram(
        win[ch], fs=sfreq, nperseg=min(T, int(sfreq * 0.5)),
    )
    keep = f <= 45
    spec = 10 * np.log10(Sxx[keep] + 1e-20)

    meta_row = run.meta[run.meta[schema.COL_WINDOW_ID] == window_id].iloc[0]

    return {
        "window_id": window_id,
        "label": meta_row[schema.COL_LABEL],
        "t_start": float(meta_row[schema.COL_T_START]),
        "t_end": float(meta_row[schema.COL_T_END]),
        "channel_names": ch_names,
        "time": t_axis,
        "traces": traces,                              # (C, P) microvolts
        "spectrogram": {
            "channel": ch_names[ch],
            "freqs": f[keep].round(2).tolist(),
            "times": t.round(3).tolist(),
            "power_db": spec.round(2).tolist(),        # (F, t)
        },
    }
