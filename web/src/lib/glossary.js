// Plain-language definitions for every state label the pipeline can produce, so
// the in-app guide can explain whatever dataset is loaded. Kept here (not in a
// component) so the data and the UI stay separate.

export const STATE_GLOSSARY = {
  // frequency bands (synthetic demo)
  delta: "0.5–4 Hz · the slowest rhythm; deep, dreamless sleep.",
  theta: "4–8 Hz · drowsiness, light sleep, and some memory tasks.",
  alpha: "8–13 Hz · relaxed wakefulness, especially with eyes closed.",
  beta: "13–30 Hz · active thinking, alertness, and motor control.",
  gamma: "30+ Hz · the fastest rhythm; attention and high-level integration.",
  mixed: "no single rhythm dominates — a blend of bands.",

  // sleep stages (sleep_edf)
  Wake: "Awake. Mixed fast activity; alpha tends to appear when the eyes close.",
  N1: "Lightest sleep — the drift out of wake. Theta begins to take over.",
  N2: "Stable light sleep. Marked by sleep spindles and K-complexes.",
  N3: "Deep slow-wave sleep. Large, slow delta waves dominate.",
  REM: "Dreaming sleep. Fast, wake-like activity paired with rapid eye movements.",

  // motor imagery (eegbci)
  rest: "Baseline — no imagined movement.",
  imagine_left: "Imagining a left-hand / left-fist movement.",
  imagine_right: "Imagining a right-hand / right-fist movement.",

  unlabeled: "No state label was assigned to this window.",
};

// What the on-canvas controls do, in the user's terms.
export const CONTROL_GUIDE = [
  ["Color: state", "Paint each point by its labeled brain state."],
  ["Color: novelty", "Shade by how unusual a window is — dark is common, bright is rare."],
  ["Trajectory", "Connect windows in time order to trace the path through the space."],
  ["Lasso", "Draw a loop around points to summarize and name that cluster."],
];

export const READING_NOTES = [
  "Each point is one short window of EEG. Near = similar; far = different.",
  "Position has no units — only relative closeness carries meaning.",
  "Band–function links are loose heuristics, not strict rules.",
];
