export default function ButtonField({ label }) {
  return (
    <button className="w-full rounded-xl py-3 font-semibold text-white shadow-md transition hover:shadow-lg bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]">
      {label}
    </button>
  );
}
