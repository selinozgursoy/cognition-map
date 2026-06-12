"""
Shared data contract for the Cognition Map pipeline.

Every pipeline stage and the API agree on these names and file layouts.
Keeping this in one place means a change to the contract is a one-line edit,
not a hunt across ten files.

Artifacts written per run (into artifacts/<dataset>/<run_hash>/):

    windows.npy      float32 (N, C, T)  raw windowed EEG, for the time-linked view
    embeddings.npy   float32 (N, D)     one vector per window (the "embed" step)
    coords.parquet   table              window_id, x, y, [z], label, novelty
    meta.parquet     table              window_id, subject, session, label, t_start, t_end
    index.faiss      binary             nearest-neighbour index over embeddings
    reducer.joblib   binary             fitted UMAP/PCA, to project new windows later
    manifest.json    json               full provenance: config, hashes, versions, shapes
"""

# ---- file names (single source of truth) -------------------------------------
WINDOWS_FILE = "windows.npy"
EMBEDDINGS_FILE = "embeddings.npy"
COORDS_FILE = "coords.parquet"
META_FILE = "meta.parquet"
INDEX_FILE = "index.faiss"
REDUCER_FILE = "reducer.joblib"
MANIFEST_FILE = "manifest.json"

# ---- column names used in meta.parquet / coords.parquet ----------------------
COL_WINDOW_ID = "window_id"   # int, 0..N-1, the atomic unit of the whole app
COL_SUBJECT = "subject"
COL_SESSION = "session"
COL_LABEL = "label"           # ground-truth or "unlabeled"
COL_T_START = "t_start"       # seconds from recording start
COL_T_END = "t_end"
COL_X = "x"                   # map coordinates
COL_Y = "y"
COL_Z = "z"
COL_NOVELTY = "novelty"       # 0..1, higher = more unusual (sparse region)

# ---- canonical EEG frequency bands (Hz) --------------------------------------
BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}
