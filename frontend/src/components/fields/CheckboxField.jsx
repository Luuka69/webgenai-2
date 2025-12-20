export default function CheckboxField({ label, value, onChange, disabled = false }) {
  return (
    <label className={`flex items-center gap-2 ${disabled ? "opacity-60" : ""}`}>
      <input
        type="checkbox"
        checked={Boolean(value)}
        onChange={(e) => onChange?.(e.target.checked)}
        disabled={disabled}
      />
      <span className="font-medium text-gray-700">{label}</span>
    </label>
  );
}

