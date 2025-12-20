export default function Sidebar({ children }) {
  return (
    <aside className="w-120 bg-white/90 backdrop-blur-md shadow-xl border-r border-gray-200 flex flex-col">  
      {children}
    </aside>
  );
}
