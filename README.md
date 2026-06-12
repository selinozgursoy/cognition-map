# Cognition Map

**Turn EEG recordings into a navigable map where similar brain states sit near each other.**

Every point is one window of brain activity. Windows with similar neural signatures land close together, so the map reveals the structure of cognition at a glance — clusters are recurring states, paths are transitions, and outliers are the moments worth a closer look.

## Why

Neural recordings are long, high-dimensional, and hard to read. Finding a handful of interesting moments means scrubbing through hours of traces. Cognition Map turns that search into spatial exploration: embed every window, project to 2D, and let the structure surface on its own.

## How it works

The heavy lifting runs once, offline. Each recording is filtered, windowed, embedded, and projected into a 2D map, and the results are written as versioned artifacts. The app only reads those artifacts — so the interface stays fast and every map is fully reproducible from its config and data.

```
ingest → preprocess → window → embed → reduce → index     offline · writes artifacts
                                                  │
                              FastAPI  ←  React + Deck.gl   online · reads artifacts
```

## What you can do

- Explore a whole recording as one interactive map, colored by brain rhythm or by how unusual each moment is
- Click any point to see its raw EEG and spectrogram
- Search for states similar to any window
- Lasso a region to get a labeled, explained cluster
- Ask why any two states are considered similar

## Quickstart

```bash
pip install -r requirements.txt
python -m pipeline.run_pipeline --config configs/default.yaml   # build a map — no download needed
uvicorn api.main:app --port 8000                                # serve it
cd web && npm install && npm run dev                            # explore at localhost:5173
```

Runs out of the box on generated EEG with known states — no download. To explore real brain data, point the pipeline at a public dataset instead.

## Datasets

The repo ships with three datasets, selected by config. The two real ones are open
PhysioNet data, fetched automatically by MNE on first use (into `~/mne_data`). The
repo never redistributes the data — each user downloads it themselves.

| Config | Dataset | What you see |
|--------|---------|--------------|
| `configs/default.yaml` | Synthetic | Generated EEG with known rhythms — runs anywhere, no download |
| `configs/sleep_edf.yaml` | [Sleep-EDF](https://physionet.org/content/sleep-edfx/) | Labeled sleep stages (Wake / N1 / N2 / N3 / REM) |
| `configs/eegbci.yaml` | [Motor Imagery](https://physionet.org/content/eegmmidb/) | Imagined movement (rest / left / right) across 64 channels |

```bash
python -m pipeline.run_pipeline --config configs/sleep_edf.yaml   # real sleep EEG
python -m pipeline.run_pipeline --config configs/eegbci.yaml      # real motor imagery
```

Each config is self-describing — edit the subject, channels, or window length and
re-run to get a new, fully reproducible map. To plug in a pretrained EEG encoder,
see [ROADMAP.md](./ROADMAP.md).

## Stack

MNE-Python · UMAP · FAISS · FastAPI · React · Deck.gl

## License

MIT
