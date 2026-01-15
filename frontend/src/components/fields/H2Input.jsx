export default function H2Input({ label, required, value, onChange, placeholder }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <label className="font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <span className="text-xs font-semibold px-2 py-1 rounded-full bg-[#A744C3]/10 text-[#6b1b84]">
          H2
        </span>
      </div>

      <input
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder ?? "Section title..."}
        className="
          w-full rounded-xl border border-gray-200 bg-white px-3 py-2
          text-base font-semibold text-gray-900
          outline-none focus:ring-2 focus:ring-[#1EB3D4]/30
        "
      />
    </div>
  );
}
