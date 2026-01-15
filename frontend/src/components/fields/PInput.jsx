export default function PInput({ label, required, value, onChange, placeholder }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <textarea
        rows={3}
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder ?? "Write text..."}
        className="
          w-full resize-none rounded-xl border border-gray-200 bg-white px-3 py-2
          text-sm text-gray-900 placeholder:text-gray-400
          outline-none focus:ring-2 focus:ring-[#1EB3D4]/30
        "
      />
    </div>
  );
}
