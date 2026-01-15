import { useMemo, useState } from "react";

const TYPE_OPTIONS = [
  "input_text",
  "input_number",
  "input_date",
  "input_email",
  "input_password",
  "textarea",
  "select",
  "input_checkbox",
  "input_boolean",
  "input_tel",
  "input_hidden",
  "pagination",
  "table",
  "button",
  "p",
  "h2",
];

function EnumEditor({ values, onChange }) {
  const safe = Array.isArray(values) ? values : [];

  const setAt = (idx, val) => {
    const next = [...safe];
    next[idx] = val;
    onChange(next.filter((x) => String(x).trim().length > 0));
  };

  const addOne = () => onChange([...(safe || []), ""]);
  const removeAt = (idx) => onChange(safe.filter((_, i) => i !== idx).filter((x) => String(x).trim().length > 0));

  return (
    <div className="space-y-2">
      {safe.map((v, idx) => (
        <div key={idx} className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
            value={v ?? ""}
            onChange={(e) => setAt(idx, e.target.value)}
            placeholder={`Value ${idx + 1}`}
          />
          <button
            type="button"
            onClick={() => removeAt(idx)}
            className="px-3 rounded-lg border border-gray-200 hover:bg-gray-50"
            title="Remove"
          >
            ✕
          </button>
        </div>
      ))}

      <button
        type="button"
        onClick={addOne}
        className="w-full py-2 rounded-lg border font-medium hover:bg-gray-50"
      >
        + Add value
      </button>
    </div>
  );
}

function TableColumnsEditor({ columns, onChange }) {
  const safe = Array.isArray(columns) ? columns : [];

  const setAt = (idx, key, val) => {
    const next = [...safe];
    next[idx] = { ...(next[idx] || {}), [key]: val };
    onChange(next.filter((c) => String(c?.key || "").trim()));
  };

  const addOne = () =>
    onChange([
      ...safe,
      { key: `COL_${safe.length + 1}`, type: "input_text", required: false, readonly: false },
    ]);

  const removeAt = (idx) => onChange(safe.filter((_, i) => i !== idx));

  return (
    <div className="space-y-2">
      {safe.length === 0 && <div className="text-xs text-gray-500">No columns yet.</div>}

      {safe.map((c, idx) => (
        <div key={idx} className="rounded-xl border border-gray-200 bg-white p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-gray-800">Column {idx + 1}</div>
            <button
              type="button"
              onClick={() => removeAt(idx)}
              className="px-2 py-1 rounded-lg border border-gray-200 hover:bg-gray-50 text-sm"
              title="Remove column"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">key</label>
              <input
                className="w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                value={c?.key ?? ""}
                onChange={(e) => setAt(idx, "key", e.target.value)}
                placeholder="ex: QTE"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">type</label>
              <select
                className="w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30 bg-white"
                value={c?.type ?? "input_text"}
                onChange={(e) => setAt(idx, "type", e.target.value)}
              >
                {TYPE_OPTIONS.filter((x) => x !== "table").map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={Boolean(c?.required)}
                onChange={(e) => setAt(idx, "required", e.target.checked)}
              />
              required
            </label>

            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={Boolean(c?.readonly)}
                onChange={(e) => setAt(idx, "readonly", e.target.checked)}
              />
              readonly
            </label>
          </div>
        </div>
      ))}

      <button
        type="button"
        onClick={addOne}
        className="w-full py-2 rounded-xl border font-semibold hover:bg-gray-50"
      >
        + Add column
      </button>
    </div>
  );
}

export default function AddFieldModal({ open, tabs = [], onClose, onSubmit }) {
  const tabsSafe = Array.isArray(tabs) ? tabs : [];
  const tabIds = useMemo(() => tabsSafe.map((t) => String(t?.ID_TAB || "")).filter(Boolean), [tabsSafe]);

  const [form, setForm] = useState({
    ID_TAB: tabIds[0] || "",
    ID_ELEMENT: "",
    TYPE_ELEMENT: "input_text",
    ACTIVE: "O",
    POSITION_X: "",
    POSITION_Y: "",
    REQUIRED: false,
    ENUM_VALUES: [],
    TABLE_COLUMNS: [],
  });

  if (!open) return null;

  const update = (key, val) => setForm((p) => ({ ...p, [key]: val }));

  const submit = () => {
    const idTab = String(form.ID_TAB || "").trim();
    const idEl = String(form.ID_ELEMENT || "").trim();
    const type = String(form.TYPE_ELEMENT || "").trim();

    if (!idTab || !idEl || !type) return;

    const payload = {
      ID_TAB: idTab,
      ID_ELEMENT: idEl,
      TYPE_ELEMENT: type,
      ACTIVE: form.ACTIVE || "O",
      VALIDATEUR_ELEMENT: { required: Boolean(form.REQUIRED) },
    };

    if (String(form.POSITION_X).trim()) payload.POSITION_X = Number(form.POSITION_X);
    if (String(form.POSITION_Y).trim()) payload.POSITION_Y = Number(form.POSITION_Y);

    if (type === "select") {
      payload.ENUM_VALUES = Array.isArray(form.ENUM_VALUES) ? form.ENUM_VALUES : [];
    }

    if (type === "table") {
      payload.CONTROL_ELEMENT = {
        table: {
          columns: Array.isArray(form.TABLE_COLUMNS) ? form.TABLE_COLUMNS : [],
        },
      };
      // table default value can be empty rows
      payload.DEFAULT_VALUE_ELEMENT = [];
    }

    onSubmit?.(payload);
  };

  const isValid =
    String(form.ID_TAB || "").trim() &&
    String(form.ID_ELEMENT || "").trim() &&
    String(form.TYPE_ELEMENT || "").trim();

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />

      <div className="fixed right-0 top-0 h-full w-[460px] bg-white z-50 shadow-2xl flex flex-col">
        <div className="p-5 text-white bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]">
          <h2 className="text-lg font-semibold">Add field</h2>
          <p className="text-sm opacity-90">Create a new element_ihm_wf without regenerating</p>
        </div>

        <div className="flex-1 overflow-auto p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">ID_TAB</label>
            <select
              value={form.ID_TAB}
              onChange={(e) => update("ID_TAB", e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30 bg-white"
            >
              {tabIds.length ? (
                tabIds.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))
              ) : (
                <option value="">(No tabs)</option>
              )}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">ID_ELEMENT</label>
            <input
              value={form.ID_ELEMENT}
              onChange={(e) => update("ID_ELEMENT", e.target.value)}
              placeholder="ex: TOTAL_HT"
              className="w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">TYPE_ELEMENT</label>
            <select
              value={form.TYPE_ELEMENT}
              onChange={(e) => update("TYPE_ELEMENT", e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30 bg-white"
            >
              {TYPE_OPTIONS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">POSITION_X (optional)</label>
              <input
                type="number"
                value={form.POSITION_X}
                onChange={(e) => update("POSITION_X", e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">POSITION_Y (optional)</label>
              <input
                type="number"
                value={form.POSITION_Y}
                onChange={(e) => update("POSITION_Y", e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-800">
              <input
                type="checkbox"
                checked={form.REQUIRED}
                onChange={(e) => update("REQUIRED", e.target.checked)}
              />
              required
            </label>

            <label className="flex items-center gap-2 text-sm text-gray-800">
              <input
                type="checkbox"
                checked={form.ACTIVE === "O"}
                onChange={(e) => update("ACTIVE", e.target.checked ? "O" : "N")}
              />
              active
            </label>
          </div>

          {form.TYPE_ELEMENT === "select" && (
            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
              <div className="text-sm font-semibold text-gray-900 mb-2">ENUM_VALUES</div>
              <EnumEditor values={form.ENUM_VALUES} onChange={(v) => update("ENUM_VALUES", v)} />
            </div>
          )}

          {form.TYPE_ELEMENT === "table" && (
            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
              <div className="text-sm font-semibold text-gray-900 mb-2">Table columns</div>
              <TableColumnsEditor
                columns={form.TABLE_COLUMNS}
                onChange={(cols) => update("TABLE_COLUMNS", cols)}
              />
              <div className="mt-2 text-xs text-gray-500">
                Stored in <code>CONTROL_ELEMENT.table.columns</code>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t flex gap-3">
          <button
            onClick={submit}
            disabled={!isValid}
            className="flex-1 py-2 text-white rounded-xl bg-gradient-to-r from-[#1EB3D4] to-[#A744C3] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
          <button onClick={onClose} className="flex-1 py-2 border rounded-xl">
            Cancel
          </button>
        </div>
      </div>
    </>
  );
}
