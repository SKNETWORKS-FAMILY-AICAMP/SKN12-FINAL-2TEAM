"use client"

import { Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { useNotifications } from "@/hooks/use-notifications"

export function NotificationDropdown() {
  const { items, unread, loading, markRead, markAllRead, remove, refresh } = useNotifications()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative h-9 w-9">
          <Bell className="h-4 w-4" />
          {unread > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 text-[10px] p-0 flex items-center justify-center bg-blue-500 text-white border-0"
            >
              {unread}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-96 bg-slate-900/90 border border-slate-700 shadow-lg backdrop-blur text-slate-100" align="end">
        <div className="px-3 py-2 flex justify-between items-center">
          <DropdownMenuLabel className="text-slate-100">알림</DropdownMenuLabel>
          <div className="flex gap-3 items-center">
            <button className="text-xs text-blue-400 hover:underline" onClick={() => markAllRead()}>모두 읽음</button>
            <button className="text-xs text-slate-300 hover:underline" onClick={() => refresh()}>새로고침</button>
          </div>
        </div>
        <DropdownMenuSeparator className="bg-slate-800" />
        <div className="max-h-96 overflow-auto">
          {loading && <div className="p-3 text-sm text-slate-400">불러오는 중...</div>}
          {!loading && items.length === 0 && (
            <div className="p-3 text-sm text-slate-400">새로운 알림이 없습니다.</div>
          )}
          {!loading && items.map((n) => (
            <DropdownMenuItem key={n.notification_id} className="flex flex-col items-start gap-1 py-2 hover:bg-slate-800/60">
              <div className="w-full flex justify-between items-center">
                <p className="text-sm font-medium text-slate-100 truncate">{n.title}</p>
                <div className="flex gap-2">
                  {!n.is_read && (
                    <button className="text-xs text-blue-400 hover:underline" onClick={(e) => { e.stopPropagation(); markRead(n.notification_id) }}>읽음</button>
                  )}
                  <button className="text-xs text-slate-300 hover:underline" onClick={(e) => { e.stopPropagation(); remove(n.notification_id) }}>삭제</button>
                </div>
              </div>
              <p className="text-xs text-slate-300/80 line-clamp-2">{n.message}</p>
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
