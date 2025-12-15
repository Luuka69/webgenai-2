import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_URL?.trim() ||
  "http://127.0.0.1:8011"; // dev fallback to backend API

function App() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [html, setHtml] = useState("");
  const [structure, setStructure] = useState(null);
  const [screenId, setScreenId] = useState("");
  const [currentScreenMeta, setCurrentScreenMeta] = useState(null);
  const [generateForWorkflow, setGenerateForWorkflow] = useState(false);
  const [screens, setScreens] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [workflowScreens, setWorkflowScreens] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [activeTab, setActiveTab] = useState("cached"); // "cached" | "workflows"
  const [isFetchingList, setIsFetchingList] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  const cachedScreens = screens.filter(
    (s) => s.kind === "cached" || !s.kind
  );
  const workflowScreensCached = screens.filter(
    (s) => s.kind === "workflow_screen"
  );

  const generateScreen = async () => {
    const trimmed = description.trim();
    if (!trimmed) {
      setError("Please enter a description before generating.");
      return;
    }

    setLoading(true);
    setError("");
    setHtml("");
    setStructure(null);
    setScreenId("");

    try {
      const body = { description: trimmed };
      if (
        generateForWorkflow &&
        currentScreenMeta?.id_client &&
        currentScreenMeta?.id_wf &&
        currentScreenMeta?.id_tache &&
        currentScreenMeta?.id_ihm
      ) {
        body.id_client = currentScreenMeta.id_client;
        body.id_wf = currentScreenMeta.id_wf;
        body.id_tache = currentScreenMeta.id_tache;
        body.id_ihm = currentScreenMeta.id_ihm;
        if (currentScreenMeta.nom_ihm) body.nom_ihm = currentScreenMeta.nom_ihm;
      }

      const response = await fetch(`${API_BASE_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }

      const newScreen = {
        id: data.id || data.screenId || "",
        kind: data.kind || "cached",
        logical_key: data.logical_key || null,
        prompt: description,
        id_client: data.id_client,
        id_wf: data.id_wf,
        id_tache: data.id_tache,
        id_ihm: data.id_ihm,
        nom_ihm: data.nom_ihm,
        title: data.screen_schema?.title || data.structure?.title || null,
      };

      setScreenId(newScreen.id);
      setStructure(data.screen_schema ?? data.structure ?? null);
      setHtml(data.code || data.html || "<p>No HTML returned.</p>");
      setCurrentScreenMeta({
        id_client: newScreen.id_client,
        id_wf: newScreen.id_wf,
        id_tache: newScreen.id_tache,
        id_ihm: newScreen.id_ihm,
        nom_ihm: newScreen.nom_ihm || null,
        kind: newScreen.kind,
      });
      setGenerateForWorkflow(Boolean(newScreen.id_client && newScreen.id_wf && newScreen.id_tache && newScreen.id_ihm));
      setScreens((prev) => {
        const idx = prev.findIndex((s) => s.id === newScreen.id);
        if (idx === -1) return [...prev, newScreen];
        const next = [...prev];
        next[idx] = { ...next[idx], ...newScreen };
        return next;
      });
      // refresh list after a successful generation
      fetchScreens();
    } catch (err) {
      console.error("Error generating screen:", err);
      const message = err instanceof Error ? err.message : "Unknown error occurred";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const fetchScreens = async () => {
    setIsFetchingList(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/screens`);
      if (!res.ok) throw new Error(`List failed: ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setScreens(data);
      } else if (data.error) {
        setError(data.error);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load screens.";
      setError(message);
    } finally {
      setIsFetchingList(false);
    }
  };

  const fetchWorkflows = async () => {
    setIsFetchingList(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/workflows`);
      if (!res.ok) throw new Error(`List workflows failed: ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setWorkflows(data);
        setWorkflowScreens([]);
        setSelectedWorkflow(null);
      } else if (data.error) {
        setError(data.error);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load workflows.";
      setError(message);
    } finally {
      setIsFetchingList(false);
    }
  };

  const fetchWorkflowScreens = async (wf) => {
    if (!wf?.id_wf) return;
    setIsFetchingList(true);
    setSelectedWorkflow(wf);
    try {
      const res = await fetch(`${API_BASE_URL}/api/workflows/${wf.id_wf}/screens`);
      if (!res.ok) throw new Error(`List workflow screens failed: ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setWorkflowScreens(data);
      } else if (data.error) {
        setError(data.error);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load workflow screens.";
      setError(message);
    } finally {
      setIsFetchingList(false);
    }
  };

  const loadScreen = async (id) => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/screens/${id}`);
      if (!res.ok) throw new Error(`Load failed: ${res.status}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setScreenId(data.id || id);
      setStructure(data.structure ?? null);
      setHtml(data.code || "<p>No HTML returned.</p>");
      if (data.prompt) setDescription(data.prompt);
      setCurrentScreenMeta({
        id_client: data.id_client,
        id_wf: data.id_wf,
        id_tache: data.id_tache,
        id_ihm: data.id_ihm,
        nom_ihm: data.nom_ihm || null,
        kind: data.kind || null,
      });
      setGenerateForWorkflow(Boolean(data.id_client && data.id_wf && data.id_tache && data.id_ihm));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load screen.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const loadWorkflowScreen = async (screen) => {
    if (!screen?.id_ihm || !screen?.id_wf) return;
    setLoading(true);
    setError("");
    if (screen.description) setDescription(screen.description);
    const url = `${API_BASE_URL}/api/screens/${screen.id_ihm}?wf_id=${screen.id_wf}`;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Load failed: ${res.status}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setScreenId(data.id || `${screen.id_wf}:${screen.id_ihm}`);
      setStructure(data.structure ?? null);
      setHtml(data.code || "<p>No HTML returned.</p>");
      setCurrentScreenMeta({
        id_client: data.id_client ?? screen.id_client,
        id_wf: data.id_wf ?? screen.id_wf,
        id_tache: data.id_tache ?? screen.id_tache,
        id_ihm: data.id_ihm ?? screen.id_ihm,
        nom_ihm: data.nom_ihm || screen.name || null,
        kind: data.kind || "workflow_screen",
      });
      setGenerateForWorkflow(true);
      // refresh cached list so it appears in saved tab
      fetchScreens();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load screen.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (activeTab === "cached") {
      fetchScreens();
    } else {
      if (selectedWorkflow) {
        fetchWorkflowScreens(selectedWorkflow);
      } else {
        fetchWorkflows();
      }
    }
  };

  const switchTab = (tab) => {
    setActiveTab(tab);
    if (tab === "cached") {
      fetchScreens();
    } else {
      fetchWorkflows();
    }
  };

  useEffect(() => {
    fetchScreens();
  }, []);

  return (
    <div className={`app-root ${showSidebar ? "" : "sidebar-hidden"}`}>
      {showSidebar && (
      <div className="sidebar">
        <div className="header">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 64 64"
            width="60"
            height="60"
            className="logo"
          >
            <defs>
              <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff4b91" />
                <stop offset="100%" stopColor="#ff77d4" />
              </linearGradient>
            </defs>
            <path
              fill="url(#brainGradient)"
              d="M32 2C18 2 8 12 8 24c0 6 3 10 6 13-1 4 0 8 3 11 3 3 8 5 15 5s12-2 15-5c3-3 4-7 3-11 3-3 6-7 6-13 0-12-10-22-24-22zm-8 6c3-1 7 1 9 4s2 7 1 10l-3-1c1-3 0-6-2-8s-5-3-7-2c-2 1-3 3-3 5h-3c0-3 2-6 5-8zm16 0c3 2 5 5 5 8h-3c0-2-1-4-3-5s-5 0-7 2-3 5-2 8l-3 1c-1-3-1-7 1-10s6-5 9-4zm-17 27c-2-1-3-2-3-3s1-2 3-3c2 1 3 2 3 3s-1 2-3 3zm18 0c-2-1-3-2-3-3s1-2 3-3c2 1 3 2 3 3s-1 2-3 3zm-9 14c-4 0-7-1-9-3s-3-4-2-7l3 1c0 2 1 4 3 5s4 2 5 2 4-1 5-2 3-3 3-5l3-1c1 3 0 5-2 7s-5 3-9 3z"
            />
          </svg>
          <h1>WebGen AI</h1>
        </div>

        <p className="subtitle">Generate a complete web page just by describing it.</p>

        <textarea
          className="description-input"
          placeholder="Example: A login page with a blue header, username & password fields, and a 'Login' button."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <button onClick={generateScreen} disabled={loading}>
          {loading ? "Generating..." : "Generate Screen"}
        </button>

        {currentScreenMeta?.id_client &&
          currentScreenMeta?.id_wf &&
          currentScreenMeta?.id_tache &&
          currentScreenMeta?.id_ihm && (
            <label className="workflow-generate-toggle">
              <input
                type="checkbox"
                checked={generateForWorkflow}
                onChange={(e) => setGenerateForWorkflow(e.target.checked)}
              />
              Update workflow screen ({currentScreenMeta.id_wf}:{currentScreenMeta.id_ihm})
            </label>
          )}

        {error && <p className="error">{error}</p>}

        {screenId && (
          <p className="info">
            Saved as <strong>{screenId}</strong>
          </p>
        )}

        {structure && (
          <pre className="structure-preview">
            {JSON.stringify(structure, null, 2)}
          </pre>
        )}

        <footer>
          <p>
            Powered by <strong>Ollama + Mistral</strong>
          </p>
        </footer>
      </div>
      )}

      <div className="output-container">
        <div className="output-header">
          <div>
            <h2>Preview</h2>
            <p className="muted">Renders the generated HTML (srcDoc) from the AI engine.</p>
          </div>
          <div className="output-actions">
            <button onClick={() => setShowSidebar((prev) => !prev)}>
              {showSidebar ? "Hide Sidebar" : "Show Sidebar"}
            </button>
            <button onClick={handleRefresh} disabled={isFetchingList}>
              {isFetchingList ? "Refreshing..." : "Refresh Screens"}
            </button>
          </div>
        </div>

        <div className="output-panels">
          <div className="preview-panel">
            {loading ? (
              <div className="loading">Loading...</div>
            ) : (
              <iframe
                title="Generated Page"
                id="generated-frame"
                srcDoc={html || "<p>No output yet.</p>"}
                sandbox="allow-scripts allow-same-origin"
              ></iframe>
            )}
          </div>
          <div className="screens-panel">
            <div className="tab-toggle">
              <button
                className={activeTab === "cached" ? "active" : ""}
                onClick={() => switchTab("cached")}
              >
                Cached
              </button>
              <button
                className={activeTab === "workflows" ? "active" : ""}
                onClick={() => switchTab("workflows")}
              >
                Workflows
              </button>
            </div>

            {activeTab === "cached" ? (
              cachedScreens.length === 0 ? (
                <p className="muted">No screens yet. Generate one to see it here.</p>
              ) : (
                <ul className="screens-list">
                  {cachedScreens.map((screen) => (
                    <li key={screen.id}>
                      <button onClick={() => loadScreen(screen.id)}>
                        {screen.id} {screen.prompt ? `- ${screen.prompt.slice(0, 32)}...` : ""}
                      </button>
                    </li>
                  ))}
                </ul>
              )
            ) : (
              <div className="workflow-browser">
                <div className="workflow-list">
                  <h4>Workflows</h4>
                  {workflows.length === 0 ? (
                    <p className="muted">No workflows loaded.</p>
                  ) : (
                    <ul className="screens-list">
                      {workflows.map((wf) => (
                        <li key={wf.id_wf}>
                          <button onClick={() => fetchWorkflowScreens(wf)}>
                            {wf.id_wf} {wf.name ? `- ${wf.name}` : ""}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="workflow-screens">
                  <h4>
                    {selectedWorkflow ? `Screens for ${selectedWorkflow.id_wf}` : "Select a workflow"}
                  </h4>
                  {selectedWorkflow && workflowScreens.length === 0 && (
                    <p className="muted">No screens for this workflow.</p>
                  )}
                  {selectedWorkflow && workflowScreens.length > 0 && (
                    <ul className="screens-list">
                      {workflowScreens.map((screen) => (
                        <li key={`${screen.id_wf}:${screen.id_ihm}`}>
                          <button onClick={() => loadWorkflowScreen(screen)}>
                            {screen.id_ihm} {screen.name ? `- ${screen.name}` : ""}{" "}
                            {screen.task_name ? `(${screen.task_name})` : ""}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                  {!selectedWorkflow && workflowScreensCached.length > 0 && (
                    <div>
                      <h4>Workflow screens (cached)</h4>
                      <ul className="screens-list">
                        {workflowScreensCached.map((screen) => {
                          const label = `${screen.id_wf || ""}:${screen.id_tache || ""}:${screen.id_ihm || ""}`.replace(/:+$/,"");
                          const title =
                            screen.nom_ihm ||
                            screen.title ||
                            (screen.prompt ? screen.prompt.slice(0, 40) : "");
                          return (
                            <li key={screen.id}>
                              <button onClick={() => loadScreen(screen.id)}>
                                {label} {title ? `- ${title}` : ""}
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
