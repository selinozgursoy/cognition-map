import { useRef, useState, useMemo, useCallback } from "react";
import DeckGL from "@deck.gl/react";
import { OrthographicView } from "@deck.gl/core";
import { ScatterplotLayer, PathLayer } from "@deck.gl/layers";
import { labelColor, noveltyColor } from "../lib/colors";
import { pointInPolygon } from "../lib/geometry";

// Component 1: the brain-state map. Every point is one EEG window; nearby points
// are similar states. GPU-rendered so it stays smooth at hundreds of thousands
// of points. Supports: color-by-band vs color-by-novelty, a time-ordered
// trajectory overlay, and freehand lasso selection for the labeling assistant.

const INITIAL_VIEW = { target: [0, 0, 0], zoom: 4 };

export default function MapCanvas({
  points,
  colorMode,          // "label" | "novelty"
  showTrajectory,
  mode,               // "explore" | "lasso"
  selectedId,
  neighborIds,
  onSelect,
  onLasso,
}) {
  const deckRef = useRef(null);
  const wrapRef = useRef(null);
  const [viewState, setViewState] = useState(INITIAL_VIEW);
  const [lasso, setLasso] = useState(null);   // array of [px, py] screen points

  const neighborSet = useMemo(() => new Set(neighborIds || []), [neighborIds]);

  const getFill = useCallback(
    (p) => (colorMode === "novelty" ? noveltyColor(p.novelty) : labelColor(p.label)),
    [colorMode]
  );

  const scatter = new ScatterplotLayer({
    id: "windows",
    data: points,
    getPosition: (p) => [p.x, p.y],
    getFillColor: getFill,
    getRadius: (p) =>
      p.window_id === selectedId ? 6 : neighborSet.has(p.window_id) ? 4 : 2.2,
    getLineColor: (p) =>
      p.window_id === selectedId
        ? [240, 244, 252]
        : neighborSet.has(p.window_id)
        ? [240, 244, 252]
        : [0, 0, 0, 0],
    getLineWidth: (p) =>
      p.window_id === selectedId ? 2 : neighborSet.has(p.window_id) ? 1.2 : 0,
    radiusUnits: "pixels",
    lineWidthUnits: "pixels",
    stroked: true,
    pickable: mode === "explore",
    onClick: (info) => info.object && onSelect(info.object.window_id),
    updateTriggers: {
      getFillColor: [colorMode],
      getRadius: [selectedId, neighborIds],
      getLineColor: [selectedId, neighborIds],
      getLineWidth: [selectedId, neighborIds],
    },
  });

  // Trajectory: connect consecutive windows (already time-ordered) into the path
  // the brain takes through latent space - loops, dwells, and drifts toward events.
  const trajectory =
    showTrajectory &&
    new PathLayer({
      id: "trajectory",
      data: [{ path: points.map((p) => [p.x, p.y]) }],
      getPath: (d) => d.path,
      getColor: [120, 130, 150, 90],
      getWidth: 1,
      widthUnits: "pixels",
    });

  const layers = [trajectory, scatter].filter(Boolean);

  // ---- lasso handling (screen space) ----------------------------------------
  const toLocal = (e) => {
    const r = wrapRef.current.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  };
  const onDown = (e) => mode === "lasso" && setLasso([toLocal(e)]);
  const onMove = (e) => mode === "lasso" && lasso && setLasso((l) => [...l, toLocal(e)]);
  const onUp = () => {
    if (mode !== "lasso" || !lasso || lasso.length < 3) return setLasso(null);
    const vp = deckRef.current?.deck?.getViewports?.()[0];
    const ids = [];
    if (vp) {
      for (const p of points) {
        const [sx, sy] = vp.project([p.x, p.y]);
        if (pointInPolygon(sx, sy, lasso)) ids.push(p.window_id);
      }
    }
    setLasso(null);
    if (ids.length) onLasso(ids);
  };

  return (
    <div
      ref={wrapRef}
      className="map-wrap"
      onMouseDown={onDown}
      onMouseMove={onMove}
      onMouseUp={onUp}
      style={{ cursor: mode === "lasso" ? "crosshair" : "grab" }}
    >
      <DeckGL
        ref={deckRef}
        views={new OrthographicView({ flipY: false })}
        viewState={viewState}
        onViewStateChange={(e) => setViewState(e.viewState)}
        controller={mode === "explore"}
        layers={layers}
        getTooltip={({ object }) =>
          object && {
            html: `<div class="tip"><b>#${object.window_id}</b> · ${object.label} · novelty ${object.novelty.toFixed(2)}</div>`,
          }
        }
      />
      {lasso && (
        <svg className="lasso-overlay">
          <polyline
            points={lasso.map((p) => p.join(",")).join(" ")}
            fill="rgba(56,116,222,0.12)"
            stroke="rgba(56,116,222,0.9)"
            strokeWidth="1.5"
          />
        </svg>
      )}
    </div>
  );
}
