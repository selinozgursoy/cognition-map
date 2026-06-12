"""
Stage 4 - Embed.

Purpose: turn each window into a single vector, so that "similar brain states"
becomes "nearby vectors". This is the step that makes the whole idea work.

Design: every backend implements the same contract -> embed(windows) -> (N, D).
That means you can ship the entire app on Tier-1 handcrafted features first, then
swap in an EEG foundation model later without touching the map, search, or UI.

Tier 1 (here): handcrafted features - zero training, fully interpretable, and good
               enough to validate the whole pipeline.
Tier 2 (hook): a pretrained EEG foundation model used as a FROZEN encoder. Models
               like EEGPT and LaBraM are designed exactly for this "frozen backbone,
               one vector per window" pattern. See _embed_foundation.
"""
from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from .schema import BANDS


def embed(windows: np.ndarray, config: dict, sfreq: float) -> np.ndarray:
    """windows: (N, C, T) -> embeddings: (N, D) float32."""
    backend = config["embed"]["backend"]
    if backend == "handcrafted":
        emb = _embed_handcrafted(windows, sfreq)
    elif backend == "foundation":
        emb = _embed_foundation(windows, config, sfreq)
    else:
        raise ValueError(f"Unknown embed backend: {backend}")

    if config["embed"].get("standardize", True) and len(emb) > 1:
        mu = emb.mean(axis=0, keepdims=True)
        sd = emb.std(axis=0, keepdims=True) + 1e-8
        emb = (emb - mu) / sd                  # z-score so no single feature dominates
    return emb.astype(np.float32)


# ----------------------------------------------------------------------------
# Tier 1: handcrafted features
# ----------------------------------------------------------------------------
def relative_band_powers(win: np.ndarray, sfreq: float):
    """Per-channel relative power in each band. Returns (band_names, (C, n_bands)).

    Shared by the embed stage and the API's explain/cluster routes, so the numbers
    the user sees in an explanation are literally the numbers that built the map.
    """
    C, T = win.shape
    nperseg = min(T, int(sfreq * 1.0))
    freqs, psd = sp_signal.welch(win, fs=sfreq, nperseg=nperseg, axis=-1)
    total = psd.sum(axis=-1, keepdims=True) + 1e-12
    cols = []
    for (lo, hi) in BANDS.values():
        mask = (freqs >= lo) & (freqs < hi)
        cols.append(psd[:, mask].sum(axis=-1, keepdims=True) / total)
    return list(BANDS.keys()), np.concatenate(cols, axis=-1)   # (C, n_bands)


def _window_features(win: np.ndarray, sfreq: float) -> np.ndarray:
    """Features for one window (C, T). Returns a flat vector.

    Per channel we compute:
      * relative power in 5 bands (delta..gamma)  -> 5
      * spectral entropy (flatness of the spectrum) -> 1
      * 3 Hjorth parameters (activity, mobility, complexity) -> 3
    So D = C * 9. These are the classic, interpretable EEG features; if a cluster
    forms, you can say *why* (e.g. "high relative alpha, occipital").
    """
    C, T = win.shape
    nperseg = min(T, int(sfreq * 1.0))         # ~1 s segments for Welch
    freqs, psd = sp_signal.welch(win, fs=sfreq, nperseg=nperseg, axis=-1)  # psd: (C, F)

    total = psd.sum(axis=-1, keepdims=True) + 1e-12
    _, rel = relative_band_powers(win, sfreq)   # (C, 5) relative band power

    p = psd / total
    spec_entropy = (-(p * np.log(p + 1e-12)).sum(axis=-1, keepdims=True)
                    / np.log(p.shape[-1]))      # (C, 1), normalised 0..1

    # Hjorth parameters from the time series.
    d1 = np.diff(win, axis=-1)
    d2 = np.diff(d1, axis=-1)
    var0 = win.var(axis=-1) + 1e-12
    var1 = d1.var(axis=-1) + 1e-12
    var2 = d2.var(axis=-1) + 1e-12
    activity = var0
    mobility = np.sqrt(var1 / var0)
    complexity = np.sqrt(var2 / var1) / mobility
    hjorth = np.stack([np.log(activity), mobility, complexity], axis=-1)   # (C, 3)

    return np.concatenate([rel, spec_entropy, hjorth], axis=-1).reshape(-1)  # (C*9,)


def _embed_handcrafted(windows: np.ndarray, sfreq: float) -> np.ndarray:
    return np.stack([_window_features(w, sfreq) for w in windows])


# ----------------------------------------------------------------------------
# Tier 2: foundation-model encoder (extension point)
# ----------------------------------------------------------------------------
def _embed_foundation(windows: np.ndarray, config: dict, sfreq: float) -> np.ndarray:
    """Use a pretrained EEG encoder as a frozen feature extractor.

    Sketch (EEGPT-style):
        import torch
        model = load_pretrained_eegpt(weights_path); model.eval()
        # EEG-FMs expect a specific sfreq (often 200-256 Hz) and channel montage,
        # so resample windows and map channels to the model's montage first.
        with torch.no_grad():
            emb = model.encode(torch.from_numpy(windows))   # (N, D)
        return emb.cpu().numpy()

    Keep the SAME (N, D) output contract and the rest of the pipeline is unchanged.
    """
    raise NotImplementedError(
        "Foundation backend is a placeholder. Start with embed.backend: handcrafted, "
        "then drop a frozen EEGPT/LaBraM encoder in here returning (N, D)."
    )
