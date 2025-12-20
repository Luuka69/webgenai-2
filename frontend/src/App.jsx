import { useEffect, useMemo, useState } from "react";
import { api } from "./services/api";

import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import MetadataRenderer from "./components/renderer/MetadataRenderer";
import FieldEditorDrawer from "./components/editor/FieldEditor";

import "./index.css";

export default function App() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [showSidebar, setShowSidebar] = useState(true);
  const [editMode, setEditMode] = useState(false);

  const [screens, setScreens] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [workflowScreens, setWorkflowScreens] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [activeTab, setActiveTab] = useState("cached");

  const [screenId, setScreenId] = useState(null);
  const [currentScreenMeta, setCurrentScreenMeta] = useState(null);

  const [elementsMeta, setElementsMeta] = useState([]);
  const [selectedElement, setSelectedElement] = useState(null);

  const [search, setSearch] = useState("");
  const [layoutCols, setLayoutCols] = useState(2); // 1 or 2
  const [formValues, setFormValues] = useState({});

  
  const cachedScreens = useMemo(
    () => screens.filter((s) => s.kind === "cached" || !s.kind),
    [screens]
  );

  const currentScreenLabel = useMemo(() => {
    if (!currentScreenMeta) return "";
    return (
      currentScreenMeta?.nom_ihm ||
      `${currentScreenMeta?.id_wf || ""}${currentScreenMeta?.id_wf ? ":" : ""}${currentScreenMeta?.id_ihm || ""}` ||
      screenId ||
      ""
    );
  }, [currentScreenMeta, screenId]);

  // ─────────────────────────────
  // API
  // ─────────────────────────────
  const fetchScreens = async () => {
    setRefreshing(true);
    try {
      const data = await api.getScreens();
      setScreens(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e?.message || "Failed to load screens");
    } finally {
      setRefreshing(false);
    }
  };

  const fetchWorkflows = async () => {
    setRefreshing(true);
    try {
      const data = await api.getWorkflows();
      setWorkflows(Array.isArray(data) ? data : []);
      setWorkflowScreens([]);
      setSelectedWorkflow(null);
    } catch (e) {
      setError(e?.message || "Failed to load workflows");
    } finally {
      setRefreshing(false);
    }
  };

  const fetchWorkflowScreens = async (wf) => {
    if (!wf?.id_wf) return;
    setRefreshing(true);
    setSelectedWorkflow(wf);
    try {
      const data = await api.getWorkflowScreens(wf.id_wf);
      setWorkflowScreens(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e?.message || "Failed to load workflow screens");
    } finally {
      setRefreshing(false);
    }
  };

  const loadScreen = async (id, params = {}) => {
    setLoading(true);
    setError("");
    try {
      const data = await api.getScreen(id, params);
      setScreenId(data.id || id);
      setElementsMeta(data.element_ihm_wf || []);
      setCurrentScreenMeta({
        id_client: data.id_client,
        id_wf: data.id_wf,
        id_tache: data.id_tache,
        id_ihm: data.id_ihm,
        nom_ihm: data.nom_ihm,
        kind: data.kind,
      });
      if (data.prompt) setDescription(data.prompt);
      setSelectedElement(null);
    } catch (e) {
      setError(e?.message || "Unable to load screen");
    } finally {
      setLoading(false);
    }
  };

  const loadWorkflowScreen = async (screen) => {
    if (!screen?.id_ihm || !screen?.id_wf) return;
    // IMPORTANT: ton backend fait /api/screens/{id_ihm}?wf_id=WF
    await loadScreen(screen.id_ihm, { wf_id: screen.id_wf });
  };

  const generateScreen = async () => {
    const trimmed = description.trim();
    if (!trimmed) return setError("Please enter a description.");

    setLoading(true);
    setError("");
    try {
      const data = await api.generate({ description: trimmed });
      // après génération, recharge la liste + load le screen généré
      await fetchScreens();
      if (data?.id) await loadScreen(data.id);
    } catch (e) {
      setError(e?.message || "Generate failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (activeTab === "cached") return fetchScreens();
    if (selectedWorkflow) return fetchWorkflowScreens(selectedWorkflow);
    return fetchWorkflows();
  };

  // ─────────────────────────────
  // EFFECT
  // ─────────────────────────────
  useEffect(() => {
    fetchScreens();
  }, []);

  // ─────────────────────────────
  // FILTER LIST UI
  // ─────────────────────────────
  const filteredCached = useMemo(() => {
    if (!search.trim()) return cachedScreens;
    const q = search.toLowerCase();
    return cachedScreens.filter((s) => (s.id || "").toLowerCase().includes(q));
  }, [cachedScreens, search]);

  // ─────────────────────────────
  // RENDER
  // ─────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        currentScreenLabel={currentScreenLabel}
        showSidebar={showSidebar}
        onToggleSidebar={() => setShowSidebar((v) => !v)}
        editMode={editMode}
        onToggleEditMode={() => {
          setEditMode((v) => !v);
          setSelectedElement(null);
        }}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        layoutCols={layoutCols}
        onSetLayoutCols={setLayoutCols}
      />

      <div className="pt-16">
        <div className="mx-auto flex max-w-[1   00px]">
          {/* SIDEBAR */}
          {showSidebar && (
            <Sidebar>
              <div className="p-4">
                <div className="rounded-2xl bg-gradient-to-r from-[#1EB3D4]/10 to-[#A744C3]/10 p-4 border border-gray-100">
                  <label className="text-xs font-semibold text-gray-600">Prompt</label>
                  {/* Prompt Box */}
                  <div className="rounded-2xl border border-gray-200 bg-white/70 shadow-sm overflow-hidden">
                    {/* Top bar */}
                    <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-[#1EB3D4]/10 to-[#A744C3]/10 border-b border-gray-200">
                      <div>
                        <p className="text-sm font-semibold text-gray-900 text-align-center">Prompt</p>
                      </div>

                    </div>

                    {/* Textarea */}
                    <div className="p-4">
                      <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={7}
                        placeholder={`Ex: Formulaire client avec:
                  - NAME (text, required)
                  - EMAIL (email, required)
                  - PASSWORD (password)
                  - DATE_OF_BIRTH (date)
                  + bouton SUBMIT (gradient)
                  + validations et messages`}
                        className="
                          w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3
                          text-sm text-gray-900 placeholder:text-gray-400
                          shadow-inner
                          focus:outline-none focus:ring-2 focus:ring-[#1EB3D4]
                          focus:border-[#1EB3D4]
                        "
                      />

                      {/* Actions */}
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <button
                          onClick={generateScreen}     // ✅ ton ancienne fonction generate
                          disabled={loading || !description.trim()}
                          className="
                            inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3
                            text-sm font-semibold text-white
                            bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]
                            shadow-lg shadow-[#A744C3]/20
                            hover:brightness-110 active:scale-[0.98] transition
                            disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
                          "
                        >
                          {loading ? "Generating..." : "Generate"}
                        </button>

                        <button
                          onClick={() => {
                            setDescription("");
                            setError("");
                          }}
                          className="
                            rounded-xl px-4 py-3 text-sm font-semibold
                            border border-gray-300 bg-white text-gray-800
                            hover:bg-gray-50 active:scale-[0.98] transition
                          "
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                  </div>
                          
                </div>

                <div className="mt-4">
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-[#A744C3]/20"
                    placeholder="Search screens..."
                  />
                </div>

                <div className="mt-4 flex rounded-xl border border-gray-200 overflow-hidden">
                  <button
                    className={`flex-1 py-2 text-sm font-semibold transition ${
                      activeTab === "cached"
                        ? "bg-gray-900 text-white"
                        : "bg-white hover:bg-gray-50"
                    }`}
                    onClick={() => {
                      setActiveTab("cached");
                      fetchScreens();
                    }}
                  >
                    Cached
                  </button>
                  <button
                    className={`flex-1 py-2 text-sm font-semibold transition ${
                      activeTab === "workflows"
                        ? "bg-gray-900 text-white"
                        : "bg-white hover:bg-gray-50"
                    }`}
                    onClick={() => {
                      setActiveTab("workflows");
                      fetchWorkflows();
                    }}
                  >
                    Workflows
                  </button>
                </div>

                {/* LISTS */}
                <div className="mt-4 space-y-2">
                  {activeTab === "cached" && (
                    <div className="space-y-2">
                      {filteredCached.map((s) => (
                        <button
                          key={s.id}
                          onClick={() => loadScreen(s.id)}
                          className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-left text-sm hover:bg-gray-50 transition"
                        >
                          <div className="font-semibold text-gray-900">{s.id}</div>
                          {s.prompt && (
                            <div className="text-xs text-gray-500 truncate">{s.prompt}</div>
                          )}
                        </button>
                      ))}
                      {!filteredCached.length && (
                        <div className="text-sm text-gray-500">No cached screens.</div>
                      )}
                    </div>
                  )}

                  {activeTab === "workflows" && (
                    <div className="space-y-3">
                      <div className="text-xs font-semibold text-gray-500">Workflows</div>
                      <div className="space-y-2">
                        {workflows.map((wf) => (
                          <button
                            key={wf.id_wf}
                            onClick={() => fetchWorkflowScreens(wf)}
                            className={`w-full rounded-xl border px-3 py-2 text-left text-sm transition ${
                              selectedWorkflow?.id_wf === wf.id_wf
                                ? "border-[#A744C3]/40 bg-[#A744C3]/5"
                                : "border-gray-200 bg-white hover:bg-gray-50"
                            }`}
                          >
                            <div className="font-semibold text-gray-900">{wf.id_wf}</div>
                            {wf.name && <div className="text-xs text-gray-500">{wf.name}</div>}
                          </button>
                        ))}
                      </div>

                      {selectedWorkflow && (
                        <>
                          <div className="text-xs font-semibold text-gray-500 mt-3">
                            Screens for {selectedWorkflow.id_wf}
                          </div>
                          <div className="space-y-2">
                            {workflowScreens.map((s) => (
                              <button
                                key={`${s.id_wf}:${s.id_ihm}`}
                                onClick={() => loadWorkflowScreen(s)}
                                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-left text-sm hover:bg-gray-50 transition"
                              >
                                <div className="font-semibold text-gray-900">{s.id_ihm}</div>
                                {(s.name || s.task_name) && (
                                  <div className="text-xs text-gray-500 truncate">
                                    {[s.name, s.task_name].filter(Boolean).join(" • ")}
                                  </div>
                                )}
                              </button>
                            ))}
                            {!workflowScreens.length && (
                              <div className="text-sm text-gray-500">No screens found.</div>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </Sidebar>
          )}

          {/* MAIN */}
          <main className="flex-1 p-6">
            {error && (
              <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700">
                {error}
              </div>
            )}

            {loading ? (
              <div className="mx-auto max-w-4xl rounded-2xl bg-white p-10 text-center text-gray-500 shadow">
                Loading...
              </div>
            ) : (
              <MetadataRenderer
                elements={elementsMeta}
                editMode={editMode}
                cols={layoutCols}
                onSelect={(el) => {
                  if (!editMode) return;
                  setSelectedElement(el);
                }}
              />

            )}
          </main>
        </div>
      </div>

      {/* EDITOR DRAWER */}
      <FieldEditorDrawer
        open={Boolean(selectedElement)}
        element={selectedElement}
        onChange={(updated) => {
          setElementsMeta((prev) =>
            prev.map((el) => (el.ID_ELEMENT === updated.ID_ELEMENT ? updated : el))
          );
          setSelectedElement(updated);
        }}
        onSave={async () => {
          if (!selectedElement || !screenId) return;
          await api.updateElement(screenId, selectedElement.ID_ELEMENT, selectedElement);
          // Optionnel: reload pour confirmer backend
          await loadScreen(screenId);
          setSelectedElement(null);
        }}
        onClose={() => setSelectedElement(null)}
      />
    </div>
  );
}
