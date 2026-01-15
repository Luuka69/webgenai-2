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

  const [tabsMeta, setTabsMeta] = useState([]);

  // ✅ Add Field panel state
  const [addFieldOpen, setAddFieldOpen] = useState(false);
  const [addingField, setAddingField] = useState(false);
  const [newField, setNewField] = useState({
    ID_TAB: "",
    ID_ELEMENT: "",
    TYPE_ELEMENT: "input_text",
    ACTIVE: "O",
    REQUIRED: false, // local UI only (will map to VALIDATEUR_ELEMENT.required)
    POSITION_X: 1,
    POSITION_Y: "", // optional (backend will auto-place if empty)
    HINT_ELEMENT: "",
    LONGEUR_ELEMENT: "",
    SQL_LOV_ELEMENT: "",
    ENUM_VALUES_TEXT: "", // comma separated
    // table:
    TABLE_COLUMNS_TEXT: "", // comma separated
  });

  const cachedScreens = useMemo(
    () => screens.filter((s) => s.kind === "cached" || !s.kind),
    [screens]
  );

  const currentScreenLabel = useMemo(() => {
    if (!currentScreenMeta) return "";
    return (
      currentScreenMeta?.nom_ihm ||
      `${currentScreenMeta?.id_wf || ""}${
        currentScreenMeta?.id_wf ? ":" : ""
      }${currentScreenMeta?.id_ihm || ""}` ||
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
      setTabsMeta(data.tab_ihm_wf || []);
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
    await loadScreen(screen.id_ihm, { wf_id: screen.id_wf });
  };

  const generateScreen = async () => {
    const trimmed = description.trim();
    if (!trimmed) return setError("Please enter a description.");

    setLoading(true);
    setError("");
    try {
      const data = await api.generate({ description: trimmed });
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
  // Add Field logic
  // ─────────────────────────────
  const openAddField = () => {
    const firstTab = Array.isArray(tabsMeta) && tabsMeta.length ? tabsMeta[0]?.ID_TAB : "";
    setNewField((prev) => ({
      ...prev,
      ID_TAB: prev.ID_TAB || firstTab || "",
      ID_ELEMENT: "",
      TYPE_ELEMENT: "input_text",
      ACTIVE: "O",
      REQUIRED: false,
      POSITION_X: 1,
      POSITION_Y: "",
      HINT_ELEMENT: "",
      LONGEUR_ELEMENT: "",
      SQL_LOV_ELEMENT: "",
      ENUM_VALUES_TEXT: "",
      TABLE_COLUMNS_TEXT: "",
    }));
    setAddFieldOpen(true);
  };

  const submitAddField = async () => {
    if (!screenId) return;
    if (!newField.ID_TAB?.trim()) return setError("Choose ID_TAB.");
    if (!newField.ID_ELEMENT?.trim()) return setError("ID_ELEMENT is required.");
    if (!newField.TYPE_ELEMENT?.trim()) return setError("TYPE_ELEMENT is required.");

    setAddingField(true);
    setError("");

    try {
      const payload = {
        ID_TAB: newField.ID_TAB.trim(),
        ID_ELEMENT: newField.ID_ELEMENT.trim(),
        TYPE_ELEMENT: newField.TYPE_ELEMENT.trim(),
        ACTIVE: newField.ACTIVE,
        POSITION_X: Number(newField.POSITION_X) || 1,
        // If empty, backend will auto-place at bottom
        ...(String(newField.POSITION_Y || "").trim()
          ? { POSITION_Y: Number(newField.POSITION_Y) || 1 }
          : {}),
        ...(newField.HINT_ELEMENT?.trim() ? { HINT_ELEMENT: newField.HINT_ELEMENT.trim() } : {}),
        ...(String(newField.LONGEUR_ELEMENT || "").trim()
          ? { LONGEUR_ELEMENT: Number(newField.LONGEUR_ELEMENT) }
          : {}),
        ...(newField.SQL_LOV_ELEMENT?.trim()
          ? { SQL_LOV_ELEMENT: newField.SQL_LOV_ELEMENT.trim() }
          : {}),
        VALIDATEUR_ELEMENT: { required: Boolean(newField.REQUIRED) },
      };

      // select enum values
      if (newField.TYPE_ELEMENT === "select") {
        const enums = (newField.ENUM_VALUES_TEXT || "")
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean);
        payload.ENUM_VALUES = enums.length ? enums : [];
      }

      // table columns (stored in CONTROL_ELEMENT.table.columns)
      if (newField.TYPE_ELEMENT === "table") {
        const cols = (newField.TABLE_COLUMNS_TEXT || "")
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean);

        payload.CONTROL_ELEMENT = {
          table: {
            columns: cols.length ? cols : ["COL1", "COL2"],
          },
        };

        // optional: default empty array to avoid “No rows” parsing issues
        payload.DEFAULT_VALUE_ELEMENT = [];
      }

      await api.addElement(screenId, payload);

      // reload screen so UI shows the new element
      await loadScreen(screenId);

      setAddFieldOpen(false);
    } catch (e) {
      setError(e?.message || "Add field failed");
    } finally {
      setAddingField(false);
    }
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
        <div className="flex ">
          {/* SIDEBAR */}
          {showSidebar && (
            <Sidebar>
              <div className="p-4">
                <div className="rounded-2xl bg-gradient-to-r from-[#1EB3D4]/10 to-[#A744C3]/10 p-4 border border-gray-100">
                  <label className="text-xs font-semibold text-gray-600">Prompt</label>

                  <div className="rounded-2xl border border-gray-200 bg-white/70 shadow-sm overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-[#1EB3D4]/10 to-[#A744C3]/10 border-b border-gray-200">
                      <div>
                        <p className="text-sm font-semibold text-gray-900 text-align-center">
                          Prompt
                        </p>
                      </div>
                    </div>

                    <div className="p-4">
                      <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={7}
                        placeholder={`Ex: Purchase screen with:
- Supplier info (text required)
- Order date (date)
- Lines table (qty, price)
+ validations`}
                        className="
                          w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3
                          text-sm text-gray-900 placeholder:text-gray-400
                          shadow-inner
                          focus:outline-none focus:ring-2 focus:ring-[#1EB3D4]
                          focus:border-[#1EB3D4]
                        "
                      />

                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <button
                          type="button"
                          onClick={generateScreen}
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
                          type="button"
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
                    type="button"
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
                    type="button"
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
                          type="button"
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
                            type="button"
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
                                type="button"
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
            {/* Top actions */}
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="text-sm text-gray-600">
                {screenId ? (
                  <>
                    Current screen: <span className="font-semibold text-gray-900">{screenId}</span>
                  </>
                ) : (
                  "Select a screen to preview."
                )}
              </div>

              <button
                type="button"
                disabled={!screenId}
                onClick={openAddField}
                className="
                  rounded-xl px-4 py-2 text-sm font-semibold text-white
                  bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]
                  hover:brightness-110 active:scale-[0.98] transition
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
              >
                + Add field
              </button>
            </div>

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
                tabs={tabsMeta}
                editMode={editMode}
                cols={layoutCols}
                onSelect={(el) => {
                  if (!editMode) return;
                  setSelectedElement(el);
                }}
                onElementMetaChange={(id, recipe) => {
                  setElementsMeta((prev) =>
                    prev.map((el) => {
                      if (el.ID_ELEMENT !== id) return el;
                      return typeof recipe === "function" ? recipe(el) : { ...el, ...recipe };
                    })
                  );
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
          await loadScreen(screenId);
          setSelectedElement(null);
        }}
        onClose={() => setSelectedElement(null)}
      />

      {/* ADD FIELD PANEL */}
      {addFieldOpen && (
        <div
          className="fixed inset-0 z-[9999] flex"
          onClick={() => setAddFieldOpen(false)} // close only when clicking backdrop
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40" />

          {/* Panel */}
          <div
            className="relative ml-auto h-full w-[460px] bg-white shadow-2xl flex flex-col pointer-events-auto"
            onClick={(e) => e.stopPropagation()} // ✅ IMPORTANT: allow clicks inside panel
          >
            <div className="p-5 text-white bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]">
              <h2 className="text-lg font-semibold">Add field</h2>
              <p className="text-sm opacity-90">Add a missing element to this screen</p>
            </div>

            <div className="flex-1 overflow-auto p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">ID_TAB</label>
                <select
                  value={newField.ID_TAB}
                  onChange={(e) => setNewField((p) => ({ ...p, ID_TAB: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                >
                  <option value="">-- Choose tab --</option>
                  {(tabsMeta || []).map((t) => (
                    <option key={t.ID_TAB} value={t.ID_TAB}>
                      {t.ID_TAB} ({t.TYPE_TAB})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">ID_ELEMENT</label>
                <input
                  value={newField.ID_ELEMENT}
                  onChange={(e) => setNewField((p) => ({ ...p, ID_ELEMENT: e.target.value }))}
                  placeholder="EX: NOM_CLIENT"
                  className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">TYPE_ELEMENT</label>
                <select
                  value={newField.TYPE_ELEMENT}
                  onChange={(e) =>
                    setNewField((p) => ({
                      ...p,
                      TYPE_ELEMENT: e.target.value,
                      // reset type-specific fields
                      ENUM_VALUES_TEXT: "",
                      TABLE_COLUMNS_TEXT: "",
                    }))
                  }
                  className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                >
                  <option value="input_text">input_text</option>
                  <option value="input_number">input_number</option>
                  <option value="input_date">input_date</option>
                  <option value="textarea">textarea</option>
                  <option value="select">select</option>
                  <option value="button">button</option>
                  <option value="table">table</option>
                  <option value="p">p</option>
                  <option value="h2">h2</option>
                </select>
              </div>

              {newField.TYPE_ELEMENT === "select" && (
                <div>
                  <label className="block text-sm font-medium mb-1">ENUM_VALUES</label>
                  <input
                    value={newField.ENUM_VALUES_TEXT}
                    onChange={(e) => setNewField((p) => ({ ...p, ENUM_VALUES_TEXT: e.target.value }))}
                    placeholder="Option1, Option2, Option3"
                    className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                  />
                  <div className="text-xs text-gray-500 mt-1">Comma separated.</div>
                </div>
              )}

              {newField.TYPE_ELEMENT === "table" && (
                <div>
                  <label className="block text-sm font-medium mb-1">Table columns</label>
                  <input
                    value={newField.TABLE_COLUMNS_TEXT}
                    onChange={(e) =>
                      setNewField((p) => ({ ...p, TABLE_COLUMNS_TEXT: e.target.value }))
                    }
                    placeholder="QTE, PRIX, POIDS"
                    className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    These go to <code>CONTROL_ELEMENT.table.columns</code>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">POSITION_X</label>
                  <input
                    type="number"
                    value={newField.POSITION_X}
                    onChange={(e) => setNewField((p) => ({ ...p, POSITION_X: e.target.value }))}
                    className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">POSITION_Y (optional)</label>
                  <input
                    type="number"
                    value={newField.POSITION_Y}
                    onChange={(e) => setNewField((p) => ({ ...p, POSITION_Y: e.target.value }))}
                    placeholder="leave empty"
                    className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Hint (optional)</label>
                <input
                  value={newField.HINT_ELEMENT}
                  onChange={(e) => setNewField((p) => ({ ...p, HINT_ELEMENT: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">SQL_LOV_ELEMENT (optional)</label>
                <textarea
                  value={newField.SQL_LOV_ELEMENT}
                  onChange={(e) =>
                    setNewField((p) => ({ ...p, SQL_LOV_ELEMENT: e.target.value }))
                  }
                  className="w-full border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30 min-h-[90px]"
                  placeholder="SELECT ... FROM ..."
                />
              </div>

              <div className="flex items-center justify-between gap-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newField.REQUIRED}
                    onChange={(e) => setNewField((p) => ({ ...p, REQUIRED: e.target.checked }))}
                  />
                  Required
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newField.ACTIVE === "O"}
                    onChange={(e) => setNewField((p) => ({ ...p, ACTIVE: e.target.checked ? "O" : "N" }))}
                  />
                  Active
                </label>
              </div>
            </div>

            <div className="p-4 border-t flex gap-3">
              <button
                type="button"
                onClick={submitAddField}
                disabled={addingField}
                className="
                  flex-1 py-2 text-white rounded-xl
                  bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]
                  hover:brightness-110 active:scale-[0.98] transition
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
              >
                {addingField ? "Adding..." : "Add"}
              </button>

              <button
                type="button"
                onClick={() => setAddFieldOpen(false)}
                className="flex-1 py-2 border rounded-xl hover:bg-gray-50 active:scale-[0.98] transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
