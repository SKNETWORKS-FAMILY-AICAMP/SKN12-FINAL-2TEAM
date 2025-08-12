import React from "react";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";
import { startRouteProgress, endRouteProgress } from "@/lib/route-progress";

interface AppSidebarProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (key: string) => void;
}

const menu = [
  { key: "dashboard", label: "대시보드" },
  { key: "portfolio", label: "포트폴리오" },
  { key: "realtime", label: "실시간 시세" },
  { key: "signals", label: "매매 시그널" },
  { key: "chat", label: "AI 채팅" },
  { key: "settings", label: "설정" },
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
          <div className="font-bold text-xl mb-4 text-white">AI Trader Pro</div>
          <div className="h-px bg-gradient-to-r from-blue-500 via-purple-500 to-transparent mb-8 opacity-60"></div>
          <nav className="flex flex-col gap-4">
            {menu.map((item) => (
              <button
                key={item.key}
                className="text-left px-3 py-2 rounded-lg hover:bg-gray-800 text-white font-medium transition-colors duration-200"
                onClick={async () => {
                  if (item.key === "chat" || item.key === "portfolio") {
                    startRouteProgress();
                  }
                  try {
                    await onNavigate(item.key);
                  } finally {
                    if (item.key === "chat" || item.key === "portfolio") {
                      // 종료 신호는 이동 후 대상 페이지에서 보내는 것이 정확하지만,
                      // fallback으로 2초 후 자동 종료
                      setTimeout(() => endRouteProgress(), 2000);
                    }
                  }
                  onClose();
                }}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <button
            className="mt-auto text-gray-400 hover:text-white text-sm font-medium py-3 px-4 rounded-lg border border-gray-600 hover:border-gray-500 hover:bg-gray-800/50 transition-all duration-200"
            onClick={onClose}
          >
            닫기
          </button>
          <button
            className="text-red-400 hover:text-red-300 text-sm font-medium py-3 px-4 rounded-lg border border-red-600/50 hover:border-red-500 hover:bg-red-900/20 mt-2 transition-all duration-200"
            onClick={handleLogout}
          >
            로그아웃
          </button>
        </div>
      </aside>
    </>
  );
} 