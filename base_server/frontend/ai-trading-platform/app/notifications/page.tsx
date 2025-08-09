"use client"

import { useNotifications } from "@/hooks/use-notifications"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function NotificationsPage() {
  const { items, unread, loading, error, refresh, markRead, markAllRead, remove } = useNotifications()

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-800 text-slate-100 px-6 py-10">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">알림</h1>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-slate-800 border-slate-700 text-slate-200">미읽음 {unread}</Badge>
            <Button variant="secondary" size="sm" onClick={() => refresh()} className="bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700/70">새로고침</Button>
            <Button variant="default" size="sm" onClick={() => markAllRead()} className="bg-blue-600 hover:bg-blue-700 text-white">모두 읽음</Button>
          </div>
        </div>

        <Card className="bg-slate-900/80 border border-slate-700 shadow-sm rounded-xl">
          <CardHeader className="border-b border-slate-800">
            <CardTitle className="text-slate-100">최근 알림</CardTitle>
          </CardHeader>
          <CardContent>
            {loading && <div className="text-slate-400 text-sm">불러오는 중...</div>}
            {error && <div className="text-red-400 text-sm mb-3">{error}</div>}
            {!loading && items.length === 0 && (
              <div className="text-slate-400 text-sm">표시할 알림이 없습니다.</div>
            )}
            <div className="space-y-4">
              {items.map((n) => (
                <div key={n.notification_id} className="flex items-start justify-between gap-4 p-4 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800/80 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-900/30 border border-blue-800 text-blue-300">{n.type_id}</span>
                      {!n.is_read && <span className="text-[11px] text-emerald-300">NEW</span>}
                    </div>
                    <div className="text-slate-100 font-medium">{n.title}</div>
                    <div className="text-sm text-slate-300/90">{n.message}</div>
                    <div className="text-xs text-slate-400 mt-1">{new Date(n.created_at).toLocaleString()}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!n.is_read && (
                      <Button size="sm" variant="secondary" className="bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700/70" onClick={() => markRead(n.notification_id)}>읽음</Button>
                    )}
                    <Button size="sm" variant="ghost" className="text-slate-300 hover:text-slate-100" onClick={() => remove(n.notification_id)}>삭제</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 