export default function TextInput({
  label,
  required,
  type = "text",
  placeholder,
  value,
  onChange,
  disabled = false,
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <input
        type={type}
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={`border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#1EB3D4] ${
          disabled ? "bg-gray-100 text-gray-500 cursor-not-allowed" : ""
        }`}
      />
    </div>
  );
}
