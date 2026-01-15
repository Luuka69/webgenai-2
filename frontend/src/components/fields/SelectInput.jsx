export default function SelectInput({
  label,
  required,
  hint,
  options = [],
  disabled,
  value,
  onChange,
}) {
  const opts = Array.isArray(options) ? options : [];

  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-semibold text-gray-800">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {hint && <p className="text-xs text-gray-500">{hint}</p>}

      <select
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:ring-2 focus:ring-[#1EB3D4]/40 disabled:bg-gray-50"
      >
        {!opts.length ? (
          <option value="">—</option>
        ) : (
          <>
            <option value="">—</option>
            {opts.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </>
        )}
      </select>
    </div>
  );
}
