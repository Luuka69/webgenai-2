export default function Pagination({ label = "Pagination", value, onChange }) {
  const page = Number.isFinite(Number(value)) ? Number(value) : 1;

  return (
    <div className="flex items-center justify-between gap-3">
      <div className="font-medium text-gray-800">{label}</div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          className="px-3 py-2 rounded-xl border hover:bg-gray-50"
          onClick={() => onChange(Math.max(1, page - 1))}
        >
          Prev
        </button>

        <div className="px-3 py-2 rounded-xl border bg-white min-w-[52px] text-center">
          {page}
        </div>

        <button
          type="button"
          className="px-3 py-2 rounded-xl border hover:bg-gray-50"
          onClick={() => onChange(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
