"use client"

import { useNotifications } from "@/hooks/use-notifications"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useEffect } from "react"

export default function NotificationsPage() {
  const { 
    notifications, 
    unreadCount, 
    isLoading, 
    error, 
    loadNotifications, 
    markAsRead, 
    markAllAsRead, 
    deleteNotification 
  } = useNotifications()

  // 컴포넌트 마운트 시 알림 로드
  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  // notifications가 undefined일 수 있으므로 안전하게 처리
  const safeNotifications = notifications || []
  const safeUnreadCount = unreadCount || 0

  // 로딩 중일 때 스켈레톤 UI 표시
  if (isLoading && safeNotifications.length === 0) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-800 text-slate-100 px-6 py-10">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">알림</h1>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-slate-800 border-slate-700 text-slate-200">미읽음 0</Badge>
              <Button variant="secondary" size="sm" disabled className="bg-slate-800 border border-slate-700 text-slate-200">새로고침</Button>
              <Button variant="default" size="sm" disabled className="bg-blue-600 text-white">모두 읽음</Button>
            </div>
          </div>
          
          <Card className="bg-slate-900/80 border border-slate-700 shadow-sm rounded-xl">
            <CardHeader className="border-b border-slate-800">
              <CardTitle className="text-slate-100">최근 알림</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-4 rounded-lg border border-slate-700 bg-slate-900 animate-pulse">
                    <div className="h-4 bg-slate-700 rounded w-1/4 mb-2"></div>
                    <div className="h-4 bg-slate-700 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-slate-700 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-800 text-slate-100 px-6 py-10">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">알림</h1>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-slate-800 border-slate-700 text-slate-200">미읽음 {safeUnreadCount}</Badge>
            <Button 
              variant="secondary" 
              size="sm" 
              onClick={() => loadNotifications()} 
              disabled={isLoading}
              className="bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700/70"
            >
              {isLoading ? "로딩 중..." : "새로고침"}
            </Button>
            <Button 
              variant="default" 
              size="sm" 
              onClick={() => markAllAsRead()} 
              disabled={isLoading || safeNotifications.length === 0}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              모두 읽음
            </Button>
          </div>
        </div>

        <Card className="bg-slate-900/80 border border-slate-700 shadow-sm rounded-xl">
          <CardHeader className="border-b border-slate-800">
            <CardTitle className="text-slate-100">최근 알림</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading && <div className="text-slate-400 text-sm mb-3">새로고침 중...</div>}
            {error && (
              <div className="text-red-400 text-sm mb-3 p-3 bg-red-900/20 border border-red-800 rounded-lg">
                <div className="font-medium">에러 코드: {error.code}</div>
                <div>{error.message}</div>
                {error.details && <div className="text-xs mt-1">{error.details}</div>}
              </div>
            )}
            {!isLoading && safeNotifications.length === 0 && (
              <div className="text-slate-400 text-sm text-center py-8">표시할 알림이 없습니다.</div>
            )}
            <div className="space-y-4">
              {safeNotifications.map((notification) => (
                <div key={notification.id} className="flex items-start justify-between gap-4 p-4 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800/80 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-900/30 border border-blue-800 text-blue-300">
                        {notification.type}
                      </span>
                      {!notification.isRead && (
                        <span className="text-[11px] text-emerald-300">NEW</span>
                      )}
                    </div>
                    <div className="text-slate-100 font-medium">{notification.title}</div>
                    <div className="text-sm text-slate-300/90">{notification.message}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {new Date(notification.createdAt).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!notification.isRead && (
                      <Button 
                        size="sm" 
                        variant="secondary" 
                        className="bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700/70" 
                        onClick={() => markAsRead(notification.id)}
                        disabled={isLoading}
                      >
                        읽음
                      </Button>
                    )}
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      className="text-slate-300 hover:text-slate-100" 
                      onClick={() => deleteNotification(notification.id)}
                      disabled={isLoading}
                    >
                      삭제
                    </Button>
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