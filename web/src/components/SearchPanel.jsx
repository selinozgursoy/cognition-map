import { rgbCss, labelColor } from "../lib/colors";

// Component 3: similarity search. Lists the windows most similar to the selected
// one (found in the full embedding space, not the 2D map). Clicking a result
// jumps the inspector to it; the matches are also highlighted on the canvas.

export default function SearchPanel({ results, onSelect }) {
  if (!results) return null;
  return (
    <div className="inspector-block">
      <div className="block-head">
        <span className="kicker">similar states</span>
        <span className="mono dim">{results.length} nearest</span>
      </div>
      <ul className="result-list">
        {results.map((r) => (
          <li key={r.window_id} onClick={() => onSelect(r.window_id)}>
            <span className="dot" style={{ background: rgbCss(labelColor(r.label)) }} />
            <span className="mono">#{r.window_id}</span>
            <span className="pill sm">{r.label}</span>
            <span className="bar">
              <span className="bar-fill" style={{ width: `${Math.max(0, r.similarity) * 100}%` }} />
            </span>
            <span className="mono dim">{r.similarity.toFixed(3)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
