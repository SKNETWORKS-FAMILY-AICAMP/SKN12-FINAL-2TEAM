"use client"

import type React from "react"
import { useState } from "react"
import {
  HomeIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  CogIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  BoltIcon,
} from "@heroicons/react/24/outline"

interface LayoutProps {
  children: React.ReactNode
  currentPage: string
  onPageChange: (page: string) => void
}

const navigation = [
  { name: "대시보드", href: "dashboard", icon: HomeIcon },
  { name: "포트폴리오", href: "portfolio", icon: ChartBarIcon },
  { name: "AI 채팅", href: "ai-chat", icon: ChatBubbleLeftRightIcon },
  { name: "자동매매", href: "auto-trading", icon: BoltIcon },
  { name: "설정", href: "settings", icon: CogIcon },
]

export default function Layout({ children, currentPage, onPageChange }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-slate-900">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? "block" : "hidden"}`}>
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-black/95 backdrop-blur-sm border-r border-gray-800/50">
          <div className="flex h-16 items-center justify-between px-4">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
              기가 버핏
            </h1>
            <button onClick={() => setSidebarOpen(false)} className="text-gray-300 hover:text-white transition-colors">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4 sidebar-nav">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => {
                  onPageChange(item.href)
                  setSidebarOpen(false)
                }}
                className={`group flex w-full items-center rounded-lg px-3 py-3 text-sm font-medium transition-all duration-300 ${
                  currentPage === item.href
                    ? "bg-gradient-to-r from-blue-500/30 to-green-500/30 text-white border border-blue-500/50 shadow-lg"
                    : "text-gray-300 hover:bg-gray-800/50 hover:text-white"
                }`}
              >
                <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                {item.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-black/50 backdrop-blur-sm border-r border-gray-800/50">
          <div className="flex h-16 items-center px-4">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
              기가 버핏
            </h1>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4 sidebar-nav">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => onPageChange(item.href)}
                className={`group flex w-full items-center rounded-lg px-3 py-3 text-sm font-medium transition-all duration-300 ${
                  currentPage === item.href
                    ? "bg-gradient-to-r from-blue-500/30 to-green-500/30 text-white border border-blue-500/50 shadow-lg"
                    : "text-gray-300 hover:bg-gray-800/50 hover:text-white"
                }`}
              >
                <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                {item.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b border-gray-800/50 bg-black/50 backdrop-blur-sm px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-300 hover:text-white lg:hidden transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1"></div>
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <button className="relative -m-2.5 p-2.5 text-gray-300 hover:text-white notification-bell transition-colors">
                <BellIcon className="h-6 w-6" />
                <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-gradient-to-r from-red-500 to-pink-500 text-xs text-white flex items-center justify-center shadow-lg">
                  3
                </span>
              </button>
              <div className="h-6 w-px bg-gray-800/50 lg:block" />
              <div className="flex items-center gap-x-2">
                <div className="h-8 w-8 rounded-full bg-gradient-to-r from-blue-500 to-green-500 flex items-center justify-center shadow-lg">
                  <span className="text-sm font-medium text-white">사</span>
                </div>
                <span className="hidden lg:block text-sm font-medium text-white">사용자</span>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">{children}</div>
        </main>
      </div>
    </div>
  )
}
