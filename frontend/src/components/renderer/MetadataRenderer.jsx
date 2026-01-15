import { useEffect, useMemo, useState } from "react";
import FieldWrapper from "./FieldWrapper";

export default function MetadataRenderer({
  elements,
  tabs = [],
  editMode,
  onSelect,
  cols = 2,
  onElementMetaChange, // ✅ NEW
}) {
  const clean = Array.isArray(elements) ? elements : [];

  const visible = useMemo(() => {
    return clean
      .filter((el) => el?.ACTIVE !== "N")
      .sort((a, b) => {
        const ay = a?.POSITION_Y ?? 0;
        const by = b?.POSITION_Y ?? 0;
        if (ay !== by) return ay - by;
        const ax = a?.POSITION_X ?? 0;
        const bx = b?.POSITION_X ?? 0;
        return ax - bx;
      });
  }, [clean]);

  // ✅ form state: ID_ELEMENT -> value
  const [values, setValues] = useState({});

  // ✅ init/reset values when elements list changes (when you load a new screen)
  useEffect(() => {
    const initial = {};
    for (const el of visible) {
      const key = el.ID_ELEMENT;

      // ✅ better defaults
      if (el.DEFAULT_VALUE_ELEMENT != null) initial[key] = el.DEFAULT_VALUE_ELEMENT;
      else if (el.TYPE_ELEMENT === "input_boolean") initial[key] = false;
      else if (el.TYPE_ELEMENT === "table") initial[key] = []; // ✅ IMPORTANT
      else initial[key] = "";
    }
    setValues(initial);
  }, [visible]);

  const setValue = (id, next) => {
    setValues((prev) => ({ ...prev, [id]: next }));
  };

  // ─────────────────────────────────────────────
  // Tabs grouping: Master (M) + Detail (D under Master)
  // ─────────────────────────────────────────────
  const tabsSafe = Array.isArray(tabs) ? tabs : [];
  const masters = tabsSafe.filter((t) => t?.TYPE_TAB === "M");
  const details = tabsSafe.filter((t) => t?.TYPE_TAB === "D");

  const masterTabIds = useMemo(
    () => new Set(masters.map((m) => String(m?.ID_TAB || ""))),
    [masters]
  );
  const detailTabIds = useMemo(
    () => new Set(details.map((d) => String(d?.ID_TAB || ""))),
    [details]
  );

  const byTab = useMemo(() => {
    const map = new Map();
    for (const el of visible) {
      const tabId = el?.ID_TAB ? String(el.ID_TAB) : "__NO_TAB__";
      if (!map.has(tabId)) map.set(tabId, []);
      map.get(tabId).push(el);
    }
    return map;
  }, [visible]);

  const gridClass = `grid gap-4 ${cols === 1 ? "grid-cols-1" : "sm:grid-cols-2"}`;

  if (!visible.length) {
    return (
      <div className="mx-auto max-w-4xl">
        <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-10 text-center">
          <div className="text-lg font-semibold text-gray-800">No elements</div>
          <p className="mt-2 text-sm text-gray-500">
            Load a screen that contains <code>element_ihm_wf</code>.
          </p>
        </div>
      </div>
    );
  }

  // Helper to render a list of elements in the standard grid
  const renderElementsGrid = (els) => (
    <div className={gridClass}>
      {els.map((el) => (
        <FieldWrapper
          key={el.ID_ELEMENT}
          element={el}
          editable={editMode}
          onSelect={onSelect}
          value={values[el.ID_ELEMENT]}
          onValueChange={(next) => setValue(el.ID_ELEMENT, next)}
          onElementMetaChange={onElementMetaChange} // ✅ NEW (this fixes your table columns persistence)
        />
      ))}
    </div>
  );

  // If we have tabs with masters, we render structured.
  const hasMasterTabs = masters.length > 0;

  // Leftover elements not belonging to any known master/detail tab:
  const leftoverElements = useMemo(() => {
    if (!hasMasterTabs) return [];
    const out = [];
    for (const el of visible) {
      const tabId = el?.ID_TAB ? String(el.ID_TAB) : "__NO_TAB__";
      const isKnown = masterTabIds.has(tabId) || detailTabIds.has(tabId);
      if (!isKnown) out.push(el);
    }
    return out;
  }, [hasMasterTabs, visible, masterTabIds, detailTabIds]);

  return (
    <div className="mx-auto max-w-5xl">
      <div className="rounded-3xl bg-white shadow-xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b bg-gradient-to-r from-[#1EB3D4]/10 to-[#A744C3]/10">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-lg font-bold text-gray-900">Screen Preview</div>
              <div className="text-sm text-gray-600">
                {editMode ? "Click a field to edit it" : "Turn on Edit Mode to edit fields"}
              </div>
            </div>
            <span
              className={`text-xs font-semibold px-3 py-1 rounded-full ${
                editMode ? "bg-[#A744C3]/15 text-[#6b1b84]" : "bg-gray-100 text-gray-600"
              }`}
            >
              {editMode ? "EDITING" : "PREVIEW"}
            </span>
          </div>
        </div>

        <div className="p-6">
          {/* ✅ MASTER/DETAIL layout */}
          {hasMasterTabs ? (
            <div className="space-y-6">
              {masters.map((m) => {
                const masterTabId = String(m?.ID_TAB || "");
                const masterEls = byTab.get(masterTabId) || [];

                const linkedDetails = details.filter(
                  (d) => String(d?.ID_TAB_MAITRE || "") === masterTabId
                );

                return (
                  <div key={masterTabId} className="rounded-2xl border border-gray-200 overflow-hidden">
                    {/* Master header */}
                    <div className="px-4 py-3 border-b bg-gradient-to-r from-[#1EB3D4]/10 to-[#A744C3]/10 flex items-center justify-between">
                      <div className="text-sm font-semibold text-gray-900">{masterTabId}</div>
                      <span className="text-xs font-semibold px-2 py-1 rounded-full bg-[#1EB3D4]/15 text-[#0b6a7c]">
                        Master
                      </span>
                    </div>

                    {/* Master fields */}
                    <div className="p-4">
                      {masterEls.length ? (
                        renderElementsGrid(masterEls)
                      ) : (
                        <div className="text-sm text-gray-500">No master elements.</div>
                      )}

                      {/* Detail blocks */}
                      {linkedDetails.map((d) => {
                        const detailTabId = String(d?.ID_TAB || "");
                        const detailEls = byTab.get(detailTabId) || [];

                        return (
                          <div
                            key={detailTabId}
                            className="mt-5 rounded-2xl border border-gray-200 bg-gray-50 overflow-hidden"
                          >
                            <div className="px-4 py-2 border-b bg-white flex items-center justify-between">
                              <div className="text-sm font-semibold text-gray-800">{detailTabId}</div>
                              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-[#A744C3]/15 text-[#6b1b84]">
                                Detail
                              </span>
                            </div>

                            <div className="p-4">
                              {detailEls.length ? (
                                renderElementsGrid(detailEls)
                              ) : (
                                <div className="text-sm text-gray-500">No detail elements.</div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}

              {/* Leftovers / non-tabbed */}
              {leftoverElements.length ? (
                <div className="rounded-2xl border border-gray-200 overflow-hidden">
                  <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                    <div className="text-sm font-semibold text-gray-900">Other fields</div>
                    <span className="text-xs font-semibold px-2 py-1 rounded-full bg-gray-200 text-gray-700">
                      Misc
                    </span>
                  </div>
                  <div className="p-4">{renderElementsGrid(leftoverElements)}</div>
                </div>
              ) : null}
            </div>
          ) : (
            /* ✅ No tabs? fallback to old behavior */
            renderElementsGrid(visible)
          )}
        </div>
      </div>
    </div>
  );
}
