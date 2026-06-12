// Thin client for the Cognition Map API. One function per endpoint, so components
// never build URLs by hand. Base URL is overridable for deployment.
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

async function get(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}
async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export const api = {
  manifest: () => get("/manifest"),
  map: () => get("/map"),
  window: (id) => get(`/window/${id}`),
  search: (window_id, k = 12) => post("/search", { window_id, k }),
  novelty: (limit = 20) => get(`/novelty?limit=${limit}`),
  labelCluster: (window_ids) => post("/cluster/label", { window_ids }),
  explainSimilarity: (window_id, neighbor_id) =>
    post("/explain/similarity", { window_id, neighbor_id }),
  explainCluster: (window_ids) => post("/explain/cluster", { window_ids }),
};
