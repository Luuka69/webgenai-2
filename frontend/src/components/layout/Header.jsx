export default function Header({
  title = "WebGen AI",
  subtitle = "Metadata-driven UI Builder",
  currentScreenLabel,
  showSidebar,
  onToggleSidebar,
  editMode,
  onToggleEditMode,
  onRefresh,
  refreshing,
  layoutCols,
  onSetLayoutCols,
}) {
  return (
    <header className="fixed top-0 left-0 right-0 z-40 border-b border-white/10 bg-gradient-to-r from-[#1EB3D4] to-[#A744C3]">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-white/15 text-white font-bold">
            W
          </div>
          <div className="leading-tight">
            <div className="text-white text-lg font-semibold">{title}</div>
            <div className="text-white/80 text-xs">{subtitle}</div>
          </div>
        </div>

        <div className="hidden md:block text-white/90 text-sm">
          {currentScreenLabel ? (
            <span className="rounded-full bg-white/15 px-3 py-1">
              {currentScreenLabel}
            </span>
          ) : (
            <span className="text-white/70">No screen selected</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="rounded-lg bg-white/15 px-3 py-2 text-sm font-semibold text-white hover:bg-white/20 transition disabled:opacity-60"
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>

          <button
            onClick={onToggleEditMode}
            className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${
              editMode
                ? "bg-white text-gray-900"
                : "bg-white/15 text-white hover:bg-white/20"
            }`}
          >
            {editMode ? "Edit Mode: ON" : "Edit Mode: OFF"}
          </button>

          <button
            onClick={onToggleSidebar}
            className="rounded-lg bg-white/15 px-3 py-2 text-sm font-semibold text-white hover:bg-white/20 transition"
          >
            {showSidebar ? "Hide" : "Show"}
          </button>
          <div className="hidden sm:flex items-center overflow-hidden rounded-lg border border-white/20">
            <button
                onClick={() => onSetLayoutCols(1)}
                className={`px-3 py-2 text-sm font-semibold transition ${
                layoutCols === 1 ? "bg-white text-gray-900" : "bg-white/15 text-white hover:bg-white/20"
                }`}
            >
                1 Col
            </button>
            <button
                onClick={() => onSetLayoutCols(2)}
                className={`px-3 py-2 text-sm font-semibold transition ${
                layoutCols === 2 ? "bg-white text-gray-900" : "bg-white/15 text-white hover:bg-white/20"
                }`}
            >
                2 Cols
            </button>
        </div>

        </div>
      </div>
    </header>
  );
}
