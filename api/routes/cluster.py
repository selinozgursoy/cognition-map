"""
Route for the cluster labeling assistant (component 4).

Flow: the user lassos a region of the map -> the frontend sends those window_ids ->
we compute a PHYSIOLOGICAL SUMMARY of the selection (mean band powers, dominant
rhythm, label mix) -> an LLM proposes a human-readable name and rationale.

Key design choice: we send the LLM SUMMARY STATISTICS, never raw EEG. That keeps
the request tiny, grounded, and cheap, and means the LLM reasons over interpretable
features ("frontal beta, pre-button-press") rather than hallucinating over a waveform.

If no ANTHROPIC_API_KEY is set, we fall back to a transparent rule-based name so the
feature still works offline.
"""
from __future__ import annotations

import os
from collections import Counter

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline import schema
from pipeline.embed import relative_band_powers
from ..deps import get_run

router = APIRouter()


class LabelRequest(BaseModel):
    window_ids: list[int]


def _selection_summary(run, window_ids: list[int]) -> dict:
    sfreq = run.manifest["sfreq"]
    band_names = list(schema.BANDS.keys())
    per_window = []
    for wid in window_ids:
        _, rel = relative_band_powers(run.windows[wid], sfreq)   # (C, n_bands)
        per_window.append(rel.mean(axis=0))                      # average over channels
    band_means = np.mean(per_window, axis=0)                     # (n_bands,)
    profile = {b: round(float(v), 3) for b, v in zip(band_names, band_means)}

    labels = run.meta[run.meta[schema.COL_WINDOW_ID].isin(window_ids)][schema.COL_LABEL]
    label_mix = dict(Counter(labels).most_common())

    return {
        "n_windows": len(window_ids),
        "band_profile": profile,
        "dominant_band": max(profile, key=profile.get),
        "label_mix": label_mix,
    }


def _llm_name(summary: dict) -> dict | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "You are labeling a cluster of EEG windows for a brain-state map. "
            "Given this summary, propose a short human-readable cluster name (<= 4 words) "
            "and one sentence of rationale grounded in the numbers.\n\n"
            f"Relative band power (0-1): {summary['band_profile']}\n"
            f"Dominant band: {summary['dominant_band']}\n"
            f"Existing label mix: {summary['label_mix']}\n"
            f"Window count: {summary['n_windows']}\n\n"
            "Respond as JSON: {\"name\": ..., \"rationale\": ...}"
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = "".join(b.text for b in msg.content if b.type == "text")
        return json.loads(text)
    except Exception as e:
        return {"name": None, "rationale": f"LLM call failed: {e}"}


def _heuristic_name(summary: dict) -> dict:
    band = summary["dominant_band"]
    pct = round(summary["band_profile"][band] * 100)
    return {
        "name": f"{band.capitalize()}-dominant",
        "rationale": f"{pct}% of relative power sits in the {band} band across "
                     f"{summary['n_windows']} windows.",
    }


@router.post("/cluster/label")
def label_cluster(req: LabelRequest):
    run = get_run()
    n = run.manifest["n_windows"]
    ids = [w for w in req.window_ids if 0 <= w < n]
    if not ids:
        raise HTTPException(400, "No valid window_ids in selection.")

    summary = _selection_summary(run, ids)
    suggestion = _llm_name(summary) or _heuristic_name(summary)
    suggestion["source"] = "llm" if os.environ.get("ANTHROPIC_API_KEY") else "heuristic"
    return {"summary": summary, "suggestion": suggestion}
