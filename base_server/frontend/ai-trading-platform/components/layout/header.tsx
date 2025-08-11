"use client"

import { Badge } from "@/components/ui/badge"
import { Menu } from "lucide-react"
import { NotificationDropdown } from "@/components/layout/notification-dropdown"

export function Header({ onSidebarOpen = () => {} }: { onSidebarOpen?: () => void }) {
  return (
    <header className="flex h-16 items-center gap-4 border-0 bg-black/80 backdrop-blur-xl shadow-xl text-white px-6">
      {/* Sidebar Toggle Button (enabled, placeholder) */}
      <button
        type="button"
        className="flex items-center justify-center h-10 w-10 rounded-md hover:bg-white/10 dark:hover:bg-black/60 transition-colors focus:outline-none mr-2"
        aria-label="사이드바 열기"
        onClick={onSidebarOpen}
      >
        <Menu className="h-6 w-6 text-white" />
      </button>

      {/* Search removed */}

      {/* Right actions */}
      <div className="flex items-center gap-2 ml-auto">
        <Badge variant="outline" className="hidden md:flex text-emerald-200 border-emerald-700 bg-black/60">
          <div className="w-2 h-2 bg-emerald-400 rounded-full mr-1" />
          시장 개장
        </Badge>
        <NotificationDropdown />
      </div>
    </header>
  )
}
