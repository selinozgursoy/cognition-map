import { useEffect, useRef } from "react";

// Component 2: the time-linked view. When a window is selected we show its real
// multichannel EEG and a spectrogram. This is the trust-builder - the moment an
// abstract dot becomes recognizable brainwaves, the map becomes believable.

function Traces({ data }) {
  // Stacked oscilloscope-style traces, one lane per channel.
  const { time, traces, channel_names } = data;
  const W = 320, laneH = 22, pad = 6;
  const H = traces.length * laneH + pad * 2;
  const tMin = time[0], tMax = time[time.length - 1];
  const x = (t) => pad + ((t - tMin) / (tMax - tMin)) * (W - pad * 2);

  return (
    <svg className="traces" viewBox={`0 0 ${W} ${H}`} width="100%">
      {traces.map((ch, i) => {
        const lo = Math.min(...ch), hi = Math.max(...ch), span = hi - lo || 1;
        const mid = pad + i * laneH + laneH / 2;
        const y = (v) => mid - ((v - (lo + hi) / 2) / span) * (laneH * 0.8);
        const d = ch.map((v, k) => `${k ? "L" : "M"}${x(time[k]).toFixed(1)},${y(v).toFixed(1)}`).join("");
        return (
          <g key={i}>
            <text className="trace-label" x={2} y={mid + 3}>{channel_names[i]}</text>
            <path d={d} className="trace-line" />
          </g>
        );
      })}
    </svg>
  );
}

function Spectrogram({ spec }) {
  // Render power_db (F x t) to a canvas with the spectral colormap.
  const ref = useRef(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv || !spec) return;
    const P = spec.power_db;               // [F][t]
    const F = P.length, T = P[0].length;
    cv.width = T; cv.height = F;
    const ctx = cv.getContext("2d");
    const img = ctx.createImageData(T, F);
    let min = Infinity, max = -Infinity;
    for (const row of P) for (const v of row) { if (v < min) min = v; if (v > max) max = v; }
    for (let f = 0; f < F; f++) {
      for (let t = 0; t < T; t++) {
        const n = (P[f][t] - min) / (max - min + 1e-9);
        // low power -> deep slate, high power -> warm coral (matches novelty ramp)
        const r = Math.round(28 + n * 204), g = Math.round(32 + n * 64), b = Math.round(44 + n * 48);
        const idx = ((F - 1 - f) * T + t) * 4;   // flip so low freq sits at bottom
        img.data[idx] = r; img.data[idx + 1] = g; img.data[idx + 2] = b; img.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [spec]);

  return (
    <div className="spec-block">
      <div className="spec-caption">spectrogram · {spec.channel} · 0–45 Hz</div>
      <canvas ref={ref} className="spec-canvas" />
    </div>
  );
}

export default function TimeLinkedView({ windowData }) {
  if (!windowData) return <div className="empty">Select a point to inspect its EEG.</div>;
  return (
    <div className="inspector-block">
      <div className="block-head">
        <span className="kicker">window</span>
        <span className="mono">#{windowData.window_id}</span>
        <span className="pill">{windowData.label}</span>
        <span className="mono dim">{windowData.t_start}s–{windowData.t_end}s</span>
      </div>
      <Traces data={windowData} />
      <Spectrogram spec={windowData.spectrogram} />
    </div>
  );
}
