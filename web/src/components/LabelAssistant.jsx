import { rgbCss, BAND_COLORS } from "../lib/colors";

// Component 4: the cluster labeling assistant. After a lasso selection, the API
// returns a physiological summary + a suggested name (LLM if a key is set, else a
// transparent rule). The user accepts or edits - labeling goes from hours to minutes.

function BandProfile({ profile }) {
  const max = Math.max(...Object.values(profile), 0.001);
  return (
    <div className="band-profile">
      {Object.entries(profile).map(([band, v]) => (
        <div key={band} className="band-row">
          <span className="band-name">{band}</span>
          <span className="band-track">
            <span
              className="band-bar"
              style={{ width: `${(v / max) * 100}%`, background: rgbCss(BAND_COLORS[band] || [140, 140, 140]) }}
            />
          </span>
          <span className="mono dim">{v.toFixed(3)}</span>
        </div>
      ))}
    </div>
  );
}

export default function LabelAssistant({ result, onAccept, onClear }) {
  if (!result) return null;
  const { summary, suggestion } = result;
  return (
    <div className="inspector-block accent">
      <div className="block-head">
        <span className="kicker">cluster label</span>
        <span className="mono dim">{summary.n_windows} windows · {suggestion.source}</span>
      </div>
      <div className="suggestion">
        <input className="name-input" defaultValue={suggestion.name || ""} id="cluster-name" />
        <p className="rationale">{suggestion.rationale}</p>
      </div>
      <BandProfile profile={summary.band_profile} />
      <div className="row gap">
        <button className="btn primary" onClick={() => onAccept(document.getElementById("cluster-name").value)}>
          Save label
        </button>
        <button className="btn ghost" onClick={onClear}>Clear</button>
      </div>
    </div>
  );
}
