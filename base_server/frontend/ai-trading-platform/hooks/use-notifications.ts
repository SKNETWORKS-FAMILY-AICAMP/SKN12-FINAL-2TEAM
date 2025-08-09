"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  InAppNotification,
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
  getNotificationStats,
} from "@/lib/api/notification"
import { useWebSocket } from "@/providers/websocket-provider"

export function useNotifications() {
  const [items, setItems] = useState<InAppNotification[]>([])
  const [totalCount, setTotalCount] = useState(0)
  // backend unread_count snapshot (for info)
  const [backendUnread, setBackendUnread] = useState(0)
  // sticky badge: only decreases on explicit actions; refresh can raise it
  const [badgeCount, setBadgeCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const { subscribe, unsubscribe } = useWebSocket()

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await listNotifications({ read_filter: "all", limit: 50 })
      if (res.errorCode === 0) {
        setItems(res.notifications || [])
        setTotalCount(res.total_count || 0)
        const unread = res.unread_count || 0
        setBackendUnread(unread)
        // only raise badge count from backend; never lower it here
        setBadgeCount((prev) => (unread > prev ? unread : prev))
      } else {
        setError(res.message || "알림을 불러오지 못했습니다.")
      }
    } catch (e: any) {
      setError(e?.message || "알림 로드 실패")
    } finally {
      setLoading(false)
    }
  }, [])

  const markRead = useCallback(async (notificationId: string) => {
    const res = await markNotificationRead(notificationId)
    if (res.errorCode === 0) {
      setItems((prev) => prev.filter((n) => n.notification_id !== notificationId))
      setBadgeCount((c) => Math.max(0, c - 1))
    }
  }, [])

  const markAllRead = useCallback(async () => {
    const res = await markAllNotificationsRead()
    if (res.errorCode === 0) {
      setItems([])
      setBadgeCount(0)
      await refresh()
    }
  }, [refresh])

  const remove = useCallback(async (notificationId: string) => {
    const target = items.find((n) => n.notification_id === notificationId)
    const wasUnread = target ? !target.is_read : false
    const res = await deleteNotification(notificationId)
    if (res.errorCode === 0) {
      setItems((prev) => prev.filter((n) => n.notification_id !== notificationId))
      if (wasUnread) setBadgeCount((c) => Math.max(0, c - 1))
      await refresh()
    }
  }, [items, refresh])

  const fetchStats = useCallback(async () => {
    const res = await getNotificationStats(7)
    return res
  }, [])

  // 초기 로드
  useEffect(() => {
    refresh()
  }, [refresh])

  // WebSocket 구독 + 상시 폴링 (WS 이벤트 즉시 반영, 폴링은 보조)
  useEffect(() => {
    const channels = [
      "notification_created",
      "notification_read",
      "notification_deleted",
    ]

    const handler = (_data: any) => {
      refresh()
    }

    // WS 이벤트 구독 (백엔드가 푸시할 때 즉시 반영)
    channels.forEach((ch) => subscribe(ch, handler))

    // 상시 폴링: WS 연결 여부와 관계 없이 일정 주기마다 동기화
    if (!pollingRef.current) {
      pollingRef.current = setInterval(() => {
        refresh()
      }, 5000)
    }

    return () => {
      channels.forEach((ch) => unsubscribe(ch))
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [subscribe, unsubscribe, refresh])

  const unread = useMemo(() => badgeCount, [badgeCount])

  return {
    items,
    totalCount,
    unread,
    backendUnread,
    loading,
    error,
    refresh,
    markRead,
    markAllRead,
    remove,
    fetchStats,
  }
} 