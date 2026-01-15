import { useEffect, useMemo, useState } from "react";

function normalizeToRows(value) {
  if (Array.isArray(value)) return value;

  if (typeof value === "string" && value.trim()) {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) return parsed;
    } catch {
      // ignore
    }
  }
  return [];
}

function normalizeColumns(cols) {
  if (!Array.isArray(cols)) return [];
  return cols
    .map((c) => {
      if (!c) return null;
      if (typeof c === "string") return { key: c, label: c };
      if (typeof c === "object") {
        const key = String(c.key ?? c.name ?? c.id ?? "").trim();
        const label = String(c.label ?? c.title ?? key).trim();
        if (!key) return null;
        return { key, label: label || key };
      }
      return null;
    })
    .filter(Boolean);
}

function computeColumnsFromRows(rows) {
  const cols = new Set();
  for (const r of rows) {
    if (r && typeof r === "object" && !Array.isArray(r)) {
      Object.keys(r).forEach((k) => cols.add(k));
    }
  }
  const out = Array.from(cols);
  if (out.length) return out.map((k) => ({ key: k, label: k }));
  return [
    { key: "COL1", label: "COL1" },
    { key: "COL2", label: "COL2" },
  ];
}

function nextColumnKey(existingKeys) {
  let i = 1;
  while (existingKeys.has(`COL${i}`)) i += 1;
  return `COL${i}`;
}

export default function TableInput({
  label,
  required,
  value,
  onChange,
  columns, // [{key,label}] from element.CONTROL_ELEMENT.table.columns
  onColumnsChange, // callback to persist columns to element meta
}) {
  const [rows, setRows] = useState(() => normalizeToRows(value));
  const [localCols, setLocalCols] = useState(() => {
    const fromProp = normalizeColumns(columns);
    if (fromProp.length) return fromProp;
    return computeColumnsFromRows(normalizeToRows(value));
  });

  // Sync rows from parent value
  useEffect(() => {
    setRows(normalizeToRows(value));
  }, [value]);

  // Sync columns from parent meta (FieldEditor or backend updates)
  useEffect(() => {
    const fromProp = normalizeColumns(columns);
    if (fromProp.length) setLocalCols(fromProp);
  }, [columns]);

  // If no columns configured and localCols is empty, derive from rows
  useEffect(() => {
    if (!localCols?.length) {
      setLocalCols(computeColumnsFromRows(rows));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows]);

  const resolvedColumns = useMemo(() => {
    return localCols?.length ? localCols : computeColumnsFromRows(rows);
  }, [localCols, rows]);

  const commitRows = (nextRows) => {
    setRows(nextRows);
    onChange?.(nextRows);
  };

  const commitCols = (nextCols) => {
    setLocalCols(nextCols);
    onColumnsChange?.(nextCols);
  };

  const addRow = () => {
    const empty = {};
    for (const c of resolvedColumns) empty[c.key] = "";
    commitRows([...(rows || []), empty]);
  };

  const removeRow = (idx) => {
    const next = (rows || []).filter((_, i) => i !== idx);
    commitRows(next);
  };

  const setCell = (rowIdx, colKey, nextVal) => {
    const next = [...(rows || [])];
    const cur = next[rowIdx] && typeof next[rowIdx] === "object" ? next[rowIdx] : {};
    next[rowIdx] = { ...cur, [colKey]: nextVal };
    commitRows(next);
  };

  const addColumn = () => {
    const keys = new Set(resolvedColumns.map((c) => c.key));
    const key = nextColumnKey(keys);

    const nextCols = [...resolvedColumns, { key, label: key }];
    commitCols(nextCols);

    // Add the new key to all existing rows
    const nextRows = (rows || []).map((r) => {
      const cur = r && typeof r === "object" ? r : {};
      if (cur[key] !== undefined) return cur;
      return { ...cur, [key]: "" };
    });
    commitRows(nextRows);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <label className="font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={addColumn}
            className="rounded-xl px-3 py-2 text-sm font-semibold border border-gray-200 bg-white hover:bg-gray-50 active:scale-[0.98] transition"
            title="Add a column"
          >
            + Column
          </button>

          <button
            type="button"
            onClick={addRow}
            className="rounded-xl px-3 py-2 text-sm font-semibold text-white bg-gradient-to-r from-[#1EB3D4] to-[#A744C3] hover:brightness-110 active:scale-[0.98] transition"
          >
            + Row
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {resolvedColumns.map((c) => (
                <th
                  key={c.key}
                  className="text-left font-semibold text-gray-700 px-3 py-2 whitespace-nowrap"
                >
                  {c.label || c.key}
                </th>
              ))}
              <th className="w-[1%] px-3 py-2" />
            </tr>
          </thead>

          <tbody>
            {(rows || []).length ? (
              rows.map((r, idx) => (
                <tr key={idx} className="border-b last:border-b-0">
                  {resolvedColumns.map((c) => (
                    <td key={c.key} className="px-3 py-2 align-top">
                      <input
                        value={r && r[c.key] != null ? String(r[c.key]) : ""}
                        onChange={(e) => setCell(idx, c.key, e.target.value)}
                        className="w-full rounded-lg border border-gray-200 px-2 py-1.5 outline-none focus:ring-2 focus:ring-[#1EB3D4]/30"
                      />
                    </td>
                  ))}
                  <td className="px-3 py-2 align-top">
                    <button
                      type="button"
                      onClick={() => removeRow(idx)}
                      className="rounded-lg border border-gray-200 px-2 py-1.5 text-gray-600 hover:bg-gray-50"
                      title="Remove row"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={resolvedColumns.length + 1} className="px-4 py-6 text-gray-500">
                  No rows yet. Click <b>+ Row</b>.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-gray-400">
        Tip: la valeur est stockée comme <code>Array&lt;Object&gt;</code>.
      </div>
    </div>
  );
}
