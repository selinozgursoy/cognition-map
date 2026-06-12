# Roadmap

Honest status of the project, and where to take it next.

## Built and working

- **Offline pipeline**, end-to-end on synthetic data: ingest → preprocess (MNE) →
  window → embed (handcrafted features) → reduce (UMAP/PCA/t-SNE) → novelty → FAISS index.
- **Reproducible runs**: config + data hashed into a `run_hash`; full provenance in `manifest.json`.
- **API**: map, per-window EEG + spectrogram, similarity search, novelty ranking,
  cluster labeling, explainability.
- **Real datasets**, fetched via MNE: Sleep-EDF (labeled sleep stages) and the
  PhysioNet Motor Imagery set (rest / imagine left / imagine right), selectable by config.
- **Frontend**: all five components — map canvas, time-linked view, similarity
  search, lasso labeling assistant, explainability panel — plus band/novelty
  coloring and a trajectory overlay.

## Stubbed (clear extension points, contracts defined)

- **Foundation-model encoder** — `pipeline/embed.py::_embed_foundation` (frozen EEGPT/LaBraM/CBraMod).
- **Label persistence** — the labeling assistant currently keeps names client-side;
  add a `POST /api/label` that writes back to `meta.parquet`.
- **LLM cluster naming** — works the moment `ANTHROPIC_API_KEY` is set; otherwise a
  transparent rule-based name is returned.

## Next features, ranked by impact-per-effort

1. **Trajectory view, leveled up.** The overlay exists; make it the star — animate
   the path over time, color by approaching event, so you can *watch* the brain
   drift toward an error. EEG is temporal; most latent-map tools throw that away.
2. **Novelty surfaced in the UI.** The `/api/novelty` endpoint is live; add a
   "most unusual moments" list that flies the camera to each outlier.
3. **Topomap explanations.** `/api/explain/cluster` already returns per-channel band
   power — render it as an MNE scalp topomap so each region gets a physiological
   fingerprint ("occipital alpha").
4. **Cross-subject alignment.** Align two subjects' embedding spaces (Procrustes /
   CCA / optimal transport) before projecting them together, so Compare mode is
   actually meaningful. A genuinely research-grade feature.
5. **State-transition graph.** Discretize the map into clusters, build a Markov
   transition matrix over time, render it as a graph — geography becomes dynamics.
6. **Compare mode.** Load two runs (subject A vs B, session 1 vs 5, before vs after
   training) on a shared projection.

## Known limitations

- Synthetic data is intentionally simple; real EEG clusters are subtler.
- t-SNE can't project new points (use UMAP/PCA if you need to add windows to an existing map).
- FAISS Flat is exact but linear in N; switch to IVF/HNSW past ~10⁶ windows.
