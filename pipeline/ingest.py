"""
Stage 1 - Ingest.

Purpose: produce ONE standardized thing for the rest of the pipeline to consume,
no matter where the data came from: an MNE Raw object plus a per-sample label array.
Everything downstream can then assume well-formed input.

Supported datasets (set `dataset:` in the config):
  * synthetic   -> generated EEG with known states. No download; runs anywhere.
  * sleep_edf   -> Sleep-EDF Expanded (PhysioNet). Labeled sleep stages - clean,
                   well-separated clusters. The best real dataset to prove the map.
  * eegbci      -> EEG Motor Movement/Imagery (PhysioNet). Labeled motor-imagery
                   states (rest / imagine left / imagine right), 64 channels.

Both real datasets are open PhysioNet data and are fetched on first use by MNE into
its cache (~/mne_data). The repo never redistributes the data - each user downloads
it themselves, so the datasets' own licenses apply to the data, not to this code.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import mne

from .schema import BANDS


@dataclass
class Recording:
    """A loaded recording in a form every later stage understands."""
    raw: mne.io.BaseRaw          # the signal (channels x time), filtered later
    labels: np.ndarray           # per-sample label, shape (n_times,), dtype=object/str
    subject: str
    session: str


def load_recording(config: dict) -> Recording:
    """Dispatch to the loader named by config['dataset']."""
    dataset = config["dataset"]
    if dataset == "synthetic":
        return _make_synthetic(config["ingest"]["synthetic"])
    if dataset == "sleep_edf":
        return _load_sleep_edf(config["ingest"]["sleep_edf"])
    if dataset == "eegbci":
        return _load_eegbci(config["ingest"]["eegbci"])
    raise ValueError(
        f"Unknown dataset '{dataset}'. Use one of: synthetic, sleep_edf, eegbci."
    )


# ----------------------------------------------------------------------------
# Shared helper: turn MNE annotations into a per-sample label array
# ----------------------------------------------------------------------------
def _labels_from_annotations(raw: mne.io.BaseRaw, mapping: dict, default: str = "unlabeled"):
    """Map each annotated span to a label, sample by sample.

    Keeping labels per-sample (not per-epoch) lets window.py assign every window a
    majority label regardless of how the windows are sized - the windowing and the
    labels stay decoupled.
    """
    n = raw.n_times
    sfreq = raw.info["sfreq"]
    first = raw.first_time
    labels = np.full(n, default, dtype=object)
    for onset, dur, desc in zip(
        raw.annotations.onset, raw.annotations.duration, raw.annotations.description
    ):
        lab = mapping.get(desc)
        if lab is None:
            continue
        start = max(0, int(round((onset - first) * sfreq)))
        end = min(n, int(round((onset - first + dur) * sfreq)))
        if end > start:
            labels[start:end] = lab
    return labels


# ----------------------------------------------------------------------------
# synthetic
# ----------------------------------------------------------------------------
def _band_signal(band: str, n: int, sfreq: float, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / sfreq
    if band == "mixed":
        freqs = rng.uniform(4.0, 30.0, size=4)
    else:
        lo, hi = BANDS[band]
        freqs = rng.uniform(lo, hi, size=2)
    sig = np.zeros(n)
    for f in freqs:
        sig += np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    sig += 0.3 * rng.standard_normal(n)
    return sig


def _make_synthetic(cfg: dict) -> Recording:
    rng = np.random.default_rng(cfg["seed"])
    sfreq = float(cfg["sfreq"])
    n_ch = int(cfg["n_channels"])
    states = list(cfg["states"])
    total = int(cfg["minutes"] * 60 * sfreq)
    seg = int(15 * sfreq)

    data = np.zeros((n_ch, total))
    labels = np.empty(total, dtype=object)
    pos, i = 0, 0
    while pos < total:
        end = min(pos + seg, total)
        state = states[i % len(states)]
        for ch in range(n_ch):
            data[ch, pos:end] = _band_signal(state, end - pos, sfreq, rng) * (0.8 + 0.4 * rng.random())
        labels[pos:end] = state
        pos, i = end, i + 1

    data *= 20e-6
    info = mne.create_info([f"EEG{n:02d}" for n in range(n_ch)], sfreq, ch_types="eeg")
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    return Recording(raw=raw, labels=labels, subject="synthetic-01", session="1")


# ----------------------------------------------------------------------------
# Sleep-EDF (PhysioNet) - labeled sleep stages
# ----------------------------------------------------------------------------
_SLEEP_STAGES = {
    "Sleep stage W": "Wake",
    "Sleep stage 1": "N1",
    "Sleep stage 2": "N2",
    "Sleep stage 3": "N3",
    "Sleep stage 4": "N3",   # AASM merges S3+S4 into N3
    "Sleep stage R": "REM",
}


def _load_sleep_edf(cfg: dict) -> Recording:
    from mne.datasets.sleep_physionet.age import fetch_data

    subject = int(cfg.get("subject", 0))
    recording = int(cfg.get("recording", 1))
    paths = fetch_data(subjects=[subject], recording=[recording], verbose="ERROR")
    psg_file, hyp_file = paths[0]

    raw = mne.io.read_raw_edf(psg_file, preload=True, stim_channel=False, verbose="ERROR")
    raw.set_annotations(mne.read_annotations(hyp_file), verbose="ERROR")

    # Keep just the EEG channels (drop EOG/EMG/respiration/temperature).
    wanted = cfg.get("channels", ["EEG Fpz-Cz", "EEG Pz-Oz"])
    present = [c for c in wanted if c in raw.ch_names]
    raw.pick(present if present else mne.pick_types(raw.info, eeg=True))

    # Sleep-EDF recordings span ~20 h, most of it pre/post-sleep wake. Crop to the
    # annotated sleep period (+/- a margin) so the map is dense with real stages.
    margin = float(cfg.get("crop_margin_min", 30.0)) * 60.0
    sleep_descs = {"Sleep stage 1", "Sleep stage 2", "Sleep stage 3",
                   "Sleep stage 4", "Sleep stage R"}
    onsets = [o for o, d in zip(raw.annotations.onset, raw.annotations.description)
              if d in sleep_descs]
    if onsets:
        tmin = max(0.0, min(onsets) - margin - raw.first_time)
        tmax = min(raw.times[-1], max(onsets) + margin - raw.first_time)
        raw.crop(tmin=tmin, tmax=tmax)

    labels = _labels_from_annotations(raw, _SLEEP_STAGES)
    return Recording(raw=raw, labels=labels, subject=f"SC{subject:03d}", session=str(recording))


# ----------------------------------------------------------------------------
# EEG Motor Movement/Imagery (PhysioNet) - labeled motor-imagery states
# ----------------------------------------------------------------------------
# Runs 4, 8, 12 = imagine opening/closing LEFT vs RIGHT fist.
# In those runs: T0 = rest, T1 = imagine left fist, T2 = imagine right fist.
_MI_EVENTS = {"T0": "rest", "T1": "imagine_left", "T2": "imagine_right"}


def _load_eegbci(cfg: dict) -> Recording:
    from mne.datasets import eegbci

    subject = int(cfg.get("subject", 1))
    runs = list(cfg.get("runs", [4, 8, 12]))
    paths = eegbci.load_data(subject, runs, verbose="ERROR")
    raws = [mne.io.read_raw_edf(p, preload=True, verbose="ERROR") for p in paths]
    raw = mne.concatenate_raws(raws, verbose="ERROR")

    eegbci.standardize(raw)                       # rename channels to 10-20 convention
    raw.set_montage("standard_1005", verbose="ERROR")

    labels = _labels_from_annotations(raw, _MI_EVENTS, default="rest")
    return Recording(raw=raw, labels=labels, subject=f"S{subject:03d}", session="MI")
