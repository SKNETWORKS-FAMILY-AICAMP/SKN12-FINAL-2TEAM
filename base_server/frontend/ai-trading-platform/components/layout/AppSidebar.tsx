import React from "react";

interface AppSidebarProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (key: string) => void;
}

const menu = [
  { key: "dashboard", label: "Overview" },
  { key: "portfolio", label: "Portfolio" },
  { key: "signals", label: "Signals" },
  { key: "chat", label: "Chat" }, // 추가: Chat 메뉴
  { key: "settings", label: "Settings" },
];

export function AppSidebar({ open, onClose, onNavigate }: AppSidebarProps) {
  return (
    <>
      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 transition-opacity duration-300"
          onClick={onClose}
          aria-label="사이드바 닫기 오버레이"
        />
      )}
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-gradient-to-br from-[#18181c] via-[#23243a] to-[#18181c] shadow-xl border-r border-[#23243a] transition-transform duration-300
        ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex flex-col h-full p-6">
          <div className="font-bold text-xl mb-8">AI Trader Pro</div>
          <nav className="flex flex-col gap-4">
            {menu.map((item) => (
              <button
                key={item.key}
                className="text-left px-3 py-2 rounded-lg hover:bg-[#23243a] text-white/90 font-medium transition"
                onClick={() => { onNavigate(item.key); onClose(); }}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <button
            className="mt-auto text-gray-400 hover:text-white text-sm pt-8"
            onClick={onClose}
          >
            닫기
          </button>
        </div>
      </aside>
    </>
  );
} 