export default function FieldEditorDrawer({ open, element, onChange, onSave, onClose }) {
  if (!open || !element) return null;

  const update = (key, value) => onChange({ ...element, [key]: value });

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />

      <div className="fixed right-0 top-0 h-full w-[420px] bg-white z-50 shadow-2xl flex flex-col">
        <div className="p-5 text-white bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]">
          <h2 className="text-lg font-semibold">Edit Element</h2>
          <p className="text-sm opacity-90">{element.ID_ELEMENT}</p>
        </div>

        <div className="flex-1 overflow-auto p-5 space-y-4">
          <Field label="Type">
            <input value={element.TYPE_ELEMENT || ""} disabled className="input disabled" />
          </Field>

          <Field label="Length">
            <input
              type="number"
              value={element.LONGEUR_ELEMENT || ""}
              onChange={(e) => update("LONGEUR_ELEMENT", e.target.value)}
              className="input"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Position X">
              <input
                type="number"
                value={element.POSITION_X || ""}
                onChange={(e) => update("POSITION_X", e.target.value)}
                className="input"
              />
            </Field>

            <Field label="Position Y">
              <input
                type="number"
                value={element.POSITION_Y || ""}
                onChange={(e) => update("POSITION_Y", e.target.value)}
                className="input"
              />
            </Field>
          </div>

          <Field label="Hint">
            <input
              value={element.HINT_ELEMENT || ""}
              onChange={(e) => update("HINT_ELEMENT", e.target.value)}
              className="input"
            />
          </Field>

          <Field label="Default Value">
            <textarea
              value={element.DEFAULT_VALUE_ELEMENT || ""}
              onChange={(e) => update("DEFAULT_VALUE_ELEMENT", e.target.value)}
              className="input min-h-[90px]"
            />
          </Field>

          <Field label="SQL_LOV_ELEMENT">
            <textarea
              value={element.SQL_LOV_ELEMENT || ""}
              onChange={(e) => update("SQL_LOV_ELEMENT", e.target.value)}
              className="input min-h-[90px]"
              placeholder="SELECT ... FROM ..."
            />
          </Field>

          <Field label="ENUM_VALUES">
            <EnumEditor
              values={Array.isArray(element.ENUM_VALUES) ? element.ENUM_VALUES : (element.ENUM_VALUES ? [String(element.ENUM_VALUES)] : [])}
              onChange={(next) => update("ENUM_VALUES", next)}
            />
          </Field>


          <Field label="VALIDATEUR_ELEMENT (JSON)">
            <textarea
              value={JSON.stringify(element.VALIDATEUR_ELEMENT || {}, null, 2)}
              onChange={(e) => {
                try {
                  update("VALIDATEUR_ELEMENT", JSON.parse(e.target.value || "{}"));
                } catch {
                  // ignore parse errors while typing
                }
              }}
              className="input font-mono text-xs min-h-[120px]"
            />
          </Field>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={element.VALIDATEUR_ELEMENT?.required || false}
              onChange={(e) =>
                update("VALIDATEUR_ELEMENT", {
                  ...(element.VALIDATEUR_ELEMENT || {}),
                  required: e.target.checked,
                })
              }
            />
            Required
          </label>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={element.ACTIVE === "O"}
              onChange={(e) => update("ACTIVE", e.target.checked ? "O" : "N")}
            />
            Active
          </label>
        </div>

        <div className="p-4 border-t flex gap-3">
          <button
            onClick={onSave}
            className="flex-1 py-2 text-white rounded bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]"
          >
            Save
          </button>
          <button onClick={onClose} className="flex-1 py-2 border rounded">
            Cancel
          </button>
        </div>
      </div>
    </>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      {children}
    </div>
  );
}
function EnumEditor({ values, onChange }) {
  const safe = Array.isArray(values) ? values : [];

  const setAt = (idx, val) => {
    const next = [...safe];
    next[idx] = val;
    onChange(next.filter((x) => String(x).trim().length > 0));
  };

  const addOne = () => onChange([...(safe || []), ""]);

  const removeAt = (idx) => {
    const next = safe.filter((_, i) => i !== idx);
    onChange(next.filter((x) => String(x).trim().length > 0));
  };

  return (
    <div className="space-y-2">
      {safe.length === 0 && (
        <div className="text-xs text-gray-500">
          No enum values yet.
        </div>
      )}

      {safe.map((v, idx) => (
        <div key={idx} className="flex gap-2">
          <input
            className="input flex-1"
            value={v ?? ""}
            onChange={(e) => setAt(idx, e.target.value)}
            placeholder={`Value ${idx + 1}`}
          />
          <button
            type="button"
            onClick={() => removeAt(idx)}
            className="px-3 rounded-lg border hover:bg-gray-50"
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
