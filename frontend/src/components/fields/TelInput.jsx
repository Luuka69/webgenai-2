export default function TelInput({ label, required, value, onChange }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="font-medium text-gray-800">
        {label}{required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <input
        type="tel"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#1EB3D4]"
        placeholder="+216 XX XXX XXX"
      />
    </div>
  );
}
