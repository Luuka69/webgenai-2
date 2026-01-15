export default function BooleanInput({ label, required, value, onChange }) {
  const checked = value === true || value === "true" || value === "O" || value === 1;

  return (
    <div className="flex items-center justify-between gap-3">
      <label className="font-medium text-gray-800">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={[
          "relative inline-flex h-7 w-12 items-center rounded-full transition",
          checked ? "bg-[#1EB3D4]" : "bg-gray-300",
        ].join(" ")}
        aria-pressed={checked}
      >
        <span
          className={[
            "inline-block h-5 w-5 transform rounded-full bg-white shadow transition",
            checked ? "translate-x-6" : "translate-x-1",
          ].join(" ")}
        />
      </button>
    </div>
  );
}
