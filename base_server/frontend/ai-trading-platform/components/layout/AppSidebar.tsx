import React from "react";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";

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
  const { logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

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
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-gradient-to-br from-black via-gray-900 to-gray-800 shadow-xl border-r border-gray-800 transition-transform duration-300
        ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex flex-col h-full p-6">
          <div className="font-bold text-xl mb-8 text-white">AI Trader Pro</div>
          <nav className="flex flex-col gap-4">
            {menu.map((item) => (
              <button
                key={item.key}
                className="text-left px-3 py-2 rounded-lg hover:bg-gray-800 text-white font-medium transition-colors duration-200"
                onClick={() => { onNavigate(item.key); onClose(); }}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <button
            className="mt-auto text-gray-400 hover:text-white text-sm pt-8 transition-colors duration-200"
            onClick={onClose}
          >
            닫기
          </button>
          <button
            className="text-red-400 hover:text-red-300 text-sm mt-2 transition-colors duration-200"
            onClick={handleLogout}
          >
            로그아웃
          </button>
        </div>
      </aside>
    </>
  );
} 