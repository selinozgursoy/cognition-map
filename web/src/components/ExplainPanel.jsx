import { rgbCss, BAND_COLORS } from "../lib/colors";

// Component 5: the explainability layer. After a search, "why similar?" compares
// the query and a neighbour band-by-band - small differences are what drive the
// match. Grounded in the same features that built the map, so it's honest.

export default function ExplainPanel({ explanation, neighborId }) {
  if (!explanation) return null;
  return (
    <div className="inspector-block">
      <div className="block-head">
        <span className="kicker">why similar</span>
        <span className="mono dim">vs #{neighborId}</span>
      </div>
      <p className="explain-line">
        Driven by <b>{explanation.drives_match.join(" + ")}</b>; differs most in{" "}
        <b>{explanation.drives_difference.join(" + ")}</b>.
      </p>
      <table className="explain-table">
        <thead>
          <tr><th>band</th><th>query</th><th>neighbor</th><th>Δ</th></tr>
        </thead>
        <tbody>
          {explanation.bands.map((b) => (
            <tr key={b.band}>
              <td>
                <span className="dot sm" style={{ background: rgbCss(BAND_COLORS[b.band] || [140, 140, 140]) }} />
                {b.band}
              </td>
              <td className="mono">{b.query}</td>
              <td className="mono">{b.neighbor}</td>
              <td className="mono dim">{b.abs_diff}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
