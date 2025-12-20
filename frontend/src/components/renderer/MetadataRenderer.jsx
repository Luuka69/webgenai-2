import { useEffect, useMemo, useState } from "react";
import FieldWrapper from "./FieldWrapper";

export default function MetadataRenderer({ elements, editMode, onSelect, cols = 2 }) {
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
      // pick default if exists, else empty
      initial[key] =
        el.DEFAULT_VALUE_ELEMENT ??
        (el.TYPE_ELEMENT === "input_boolean" ? false : "");
    }
    setValues(initial);
  }, [visible]);

  const setValue = (id, next) => {
    setValues((prev) => ({ ...prev, [id]: next }));
  };

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
          <div className={`grid gap-4 ${cols === 1 ? "grid-cols-1" : "sm:grid-cols-2"}`}>
            {visible.map((el) => (
              <FieldWrapper
                key={el.ID_ELEMENT}
                element={el}
                editable={editMode}
                onSelect={onSelect}
                value={values[el.ID_ELEMENT]}
                onValueChange={(next) => setValue(el.ID_ELEMENT, next)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
