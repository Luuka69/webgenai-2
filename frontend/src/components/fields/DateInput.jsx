export default function DateInput({ label, required, hint, disabled, value, onChange }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-semibold text-gray-800">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {hint && <p className="text-xs text-gray-500">{hint}</p>}
      <input
        type="date"
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:ring-2 focus:ring-[#1EB3D4]/40 disabled:bg-gray-50"
      />
    </div>
  );
}
