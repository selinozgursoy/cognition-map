import { useEffect, useState, useCallback } from "react";
import { api } from "./lib/api";
import { BAND_COLORS, rgbCss } from "./lib/colors";
import MapCanvas from "./components/MapCanvas";
import TimeLinkedView from "./components/TimeLinkedView";
import SearchPanel from "./components/SearchPanel";
import LabelAssistant from "./components/LabelAssistant";
import ExplainPanel from "./components/ExplainPanel";
import GuidePanel from "./components/GuidePanel";

export default function App() {
  const [manifest, setManifest] = useState(null);
  const [points, setPoints] = useState([]);
  const [error, setError] = useState(null);

  const [colorMode, setColorMode] = useState("label");
  const [showTrajectory, setShowTrajectory] = useState(false);
  const [mode, setMode] = useState("explore");

  const [selectedId, setSelectedId] = useState(null);
  const [windowData, setWindowData] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [neighborIds, setNeighborIds] = useState([]);
  const [explanation, setExplanation] = useState(null);
  const [topNeighbor, setTopNeighbor] = useState(null);
  const [labelResult, setLabelResult] = useState(null);
  const [showGuide, setShowGuide] = useState(false);

  // Close the guide with Escape.
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && setShowGuide(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Load the map once.
  useEffect(() => {
    (async () => {
      try {
        setManifest(await api.manifest());
        setPoints((await api.map()).points);
      } catch (e) {
        setError("Can't reach the API. Start it with: uvicorn api.main:app --port 8000");
      }
    })();
  }, []);

  // When a window is selected: load its EEG, find similar states, explain the top match.
  useEffect(() => {
    if (selectedId == null) return;
    (async () => {
      const [w, s] = await Promise.all([api.window(selectedId), api.search(selectedId, 12)]);
      setWindowData(w);
      setSearchResults(s.results);
      setNeighborIds(s.results.map((r) => r.window_id));
      if (s.results.length) {
        const nb = s.results[0].window_id;
        setTopNeighbor(nb);
        setExplanation(await api.explainSimilarity(selectedId, nb));
      }
    })();
  }, [selectedId]);

  const onLasso = useCallback(async (ids) => {
    setLabelResult(await api.labelCluster(ids));
  }, []);

  const acceptLabel = (name) => {
    // For the MVP, labels live client-side. Persisting them is a /label POST away
    // (write back to meta.parquet) - left as a deliberate next step.
    alert(`Saved "${name}" for ${labelResult.summary.n_windows} windows (session-only in MVP).`);
    setLabelResult(null);
    setMode("explore");
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo-mark" />
          <div>
            <h1>Cognition Map</h1>
            <p className="sub">a navigable map of brain states</p>
          </div>
        </div>
        <div className="legend">
          {manifest &&
            manifest.labels.map((l) => (
              <span key={l} className="legend-item">
                <span className="dot" style={{ background: rgbCss(BAND_COLORS[l] || [140, 140, 140]) }} />
                {l}
              </span>
            ))}
        </div>
        <div className="run-meta mono">
          {manifest ? `${manifest.dataset} · ${manifest.n_windows} windows · run ${manifest.run_hash}` : "loading…"}
          <button className="guide-btn" onClick={() => setShowGuide(true)}>guide</button>
        </div>
      </header>

      <main className="layout">
        <section className="canvas-col">
          {error ? (
            <div className="error-state">{error}</div>
          ) : (
            <MapCanvas
              points={points}
              colorMode={colorMode}
              showTrajectory={showTrajectory}
              mode={mode}
              selectedId={selectedId}
              neighborIds={neighborIds}
              onSelect={setSelectedId}
              onLasso={onLasso}
            />
          )}
          <div className="controls">
            <div className="seg">
              <button className={colorMode === "label" ? "on" : ""} onClick={() => setColorMode("label")}>
                color: band
              </button>
              <button className={colorMode === "novelty" ? "on" : ""} onClick={() => setColorMode("novelty")}>
                color: novelty
              </button>
            </div>
            <button className={`toggle ${showTrajectory ? "on" : ""}`} onClick={() => setShowTrajectory((v) => !v)}>
              trajectory
            </button>
            <button
              className={`toggle ${mode === "lasso" ? "on" : ""}`}
              onClick={() => setMode((m) => (m === "lasso" ? "explore" : "lasso"))}
            >
              {mode === "lasso" ? "lasso: drawing" : "lasso a cluster"}
            </button>
          </div>
        </section>

        <aside className="inspector">
          {labelResult && <LabelAssistant result={labelResult} onAccept={acceptLabel} onClear={() => setLabelResult(null)} />}
          <TimeLinkedView windowData={windowData} />
          <SearchPanel results={searchResults} onSelect={setSelectedId} />
          <ExplainPanel explanation={explanation} neighborId={topNeighbor} />
        </aside>
      </main>

      {showGuide && manifest && (
        <GuidePanel labels={manifest.labels} onClose={() => setShowGuide(false)} />
      )}
    </div>
  );
}
