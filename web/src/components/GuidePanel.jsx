import { rgbCss, labelColor } from "../lib/colors";
import { STATE_GLOSSARY, CONTROL_GUIDE, READING_NOTES } from "../lib/glossary";

// A dismissible guide that explains the states present in THIS run (frequency
// bands, sleep stages, or motor-imagery states) plus what each control does.
// Opened from the header; closed by the backdrop, the X, or the Escape key.

export default function GuidePanel({ labels, onClose }) {
  return (
    <div className="guide-backdrop" onClick={onClose}>
      <div className="guide-panel" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Reading the map">
        <div className="guide-head">
          <h2>Reading the map</h2>
          <button className="guide-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <section>
          <h3>States in this run</h3>
          <ul className="guide-states">
            {labels.map((l) => (
              <li key={l}>
                <span className="dot" style={{ background: rgbCss(labelColor(l)) }} />
                <span className="guide-name">{l}</span>
                <span className="guide-def">{STATE_GLOSSARY[l] || "—"}</span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h3>Controls</h3>
          <ul className="guide-controls">
            {CONTROL_GUIDE.map(([name, desc]) => (
              <li key={name}>
                <span className="guide-name">{name}</span>
                <span className="guide-def">{desc}</span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h3>Good to know</h3>
          <ul className="guide-notes">
            {READING_NOTES.map((n) => <li key={n}>{n}</li>)}
          </ul>
        </section>
      </div>
    </div>
  );
}
