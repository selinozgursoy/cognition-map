// The spectral color system - the design signature.
// Frequency bands are ordered low -> high and colored cool -> warm, mirroring the
// physics of the spectrum. Sleep stages get a depth gradient (alert wake -> deep
// sleep, REM set apart); motor-imagery states get distinct left/right hues. In
// every case the color encodes something true about the state, never decoration.

export const BAND_COLORS = {
  // frequency bands (synthetic demo)
  delta: [110, 86, 207],
  theta: [56, 116, 222],
  alpha: [38, 178, 184],
  beta: [224, 168, 60],
  gamma: [232, 96, 92],
  mixed: [120, 130, 150],

  // sleep stages (sleep_edf): wake = alert/warm, deepening to violet, REM = coral
  Wake: [224, 168, 60],
  N1: [38, 178, 184],
  N2: [56, 116, 222],
  N3: [110, 86, 207],
  REM: [232, 96, 92],

  // motor imagery (eegbci)
  rest: [120, 130, 150],
  imagine_left: [56, 116, 222],
  imagine_right: [224, 168, 60],

  unlabeled: [90, 98, 112],
};

const FALLBACK = [150, 158, 176];

export function labelColor(label) {
  return BAND_COLORS[label] || FALLBACK;
}

export function rgbCss(rgb, alpha = 1) {
  return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${alpha})`;
}

// Sequential ramp for novelty (calm slate -> alert coral): common states recede,
// rare states glow.
export function noveltyColor(t) {
  const a = [70, 84, 110];
  const b = [232, 96, 92];
  return a.map((c, i) => Math.round(c + (b[i] - c) * t));
}
