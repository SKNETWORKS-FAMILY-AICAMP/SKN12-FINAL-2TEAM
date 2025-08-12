import { apiClient } from "@/lib/api/client"

// Types aligned with backend models in template/notification/common
export interface InAppNotification {
  idx?: number
  notification_id: string
  account_db_key: number
  type_id: string
  title: string
  message: string
  data?: Record<string, any> | null
  priority: number
  is_read: boolean
  read_at?: string | null
  expires_at?: string | null
  created_at: string
  updated_at: string
}

export interface NotificationListResponse {
  errorCode: number
  message?: string
  notifications: InAppNotification[]
  total_count: number
  unread_count: number
  has_more: boolean
}

export interface SimpleResultResponse {
  errorCode: number
  result?: string
  message?: string
  updated_count?: number
}

export interface NotificationStatsItem {
  date: string
  total_count: number
  read_count: number
  unread_count: number
  priority_1_count: number
  priority_2_count: number
  priority_3_count: number
  auto_deleted_count: number
  current_unread_count: number
}

export interface NotificationStatsResponse {
  errorCode: number
  message?: string
  daily_stats: NotificationStatsItem[]
  current_unread_count: number
}

export interface NotificationCreateParams {
  target_type?: "ALL" | "SPECIFIC_USER" | "USER_GROUP"
  target_users?: number[]
  user_group?: string
  type_id: string
  title: string
  message: string
  data?: Record<string, any>
  priority?: number
  expires_at?: string
}

export async function listNotifications(params?: {
  read_filter?: "all" | "unread_only" | "read_only"
  type_id?: string
  page?: number
  limit?: number
  days?: number // optional hint for backend stats prefetch
}) {
  const res = await apiClient.post<NotificationListResponse>(
    "/notification/list",
    {
      read_filter: params?.read_filter ?? "unread_only",
      type_id: params?.type_id,
      page: params?.page ?? 1,
      limit: params?.limit ?? 10,
      days: params?.days,
    },
  )
  return res
}

export async function markNotificationRead(notification_id: string) {
  const res = await apiClient.post<SimpleResultResponse>(
    "/notification/mark-read",
    { notification_id },
  )
  return res
}

export async function markAllNotificationsRead(type_id?: string) {
  const res = await apiClient.post<SimpleResultResponse>(
    "/notification/mark-all-read",
    { type_id },
  )
  return res
}

export async function deleteNotification(notification_id: string) {
  const res = await apiClient.post<SimpleResultResponse>(
    "/notification/delete",
    { notification_id },
  )
  return res
}

export async function getNotificationStats(days = 7) {
  const res = await apiClient.post<NotificationStatsResponse>(
    "/notification/stats",
    { days },
  )
  return res
}

export async function createNotification(params: NotificationCreateParams) {
  const res = await apiClient.post<SimpleResultResponse>(
    "/notification/create",
    params,
  )
  return res
}