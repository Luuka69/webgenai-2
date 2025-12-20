const API_BASE_URL =
  import.meta.env.VITE_API_URL?.trim() || "http://127.0.0.1:8011";

async function jsonOrThrow(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data?.error || `Request failed (${res.status})`);
  }
  if (data?.error) throw new Error(data.error);
  return data;
}

export const api = {
  // Screens
  getScreens: async () => jsonOrThrow(await fetch(`${API_BASE_URL}/api/screens`)),
  getScreen: async (id, params = {}) => {
    const url = new URL(`${API_BASE_URL}/api/screens/${id}`);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
    return jsonOrThrow(await fetch(url));
  },

  // Workflows
  getWorkflows: async () => jsonOrThrow(await fetch(`${API_BASE_URL}/api/workflows`)),
  getWorkflowScreens: async (wfId) =>
    jsonOrThrow(await fetch(`${API_BASE_URL}/api/workflows/${wfId}/screens`)),

  // Generate
  generate: async (payload) =>
    jsonOrThrow(
      await fetch(`${API_BASE_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
    ),

  // Update element
  updateElement: async (screenId, elementId, payload) =>
    jsonOrThrow(
      await fetch(`${API_BASE_URL}/api/screens/${screenId}/elements/${elementId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
    ),
};
