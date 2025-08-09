import { apiClient } from "@/lib/api/client"

// Minimal types aligned with backend models
export interface SignalAlarmInfo {
  alarm_id: string
  symbol: string
  company_name: string
  current_price: number
  exchange: string
  currency: string
  note: string
  is_active: boolean
  signal_count: number
  win_rate: number
  profit_rate: number
  created_at: string
}

export interface SignalAlarmCreateResponse {
  errorCode: number
  alarm_id?: string
  alarm_info?: SignalAlarmInfo
  message?: string
}

export interface SignalAlarmListResponse {
  errorCode: number
  alarms?: SignalAlarmInfo[]
  total_count?: number
  active_count?: number
  message?: string
}

export interface SignalAlarmToggleResponse {
  errorCode: number
  alarm_id?: string
  is_active?: boolean
  message?: string
}

export interface SignalAlarmDeleteResponse {
  errorCode: number
  alarm_id?: string
  message?: string
}

export async function createSignalAlarm(params: { symbol: string; note?: string }) {
  const res = await apiClient.post<SignalAlarmCreateResponse>(
    "/autotrade/signal/alarm/create",
    params,
  )
  return res
}

export async function listSignalAlarms() {
  const res = await apiClient.post<SignalAlarmListResponse>(
    "/autotrade/signal/alarm/list",
    {},
  )
  return res
}

export async function toggleSignalAlarm(alarm_id: string) {
  const res = await apiClient.post<SignalAlarmToggleResponse>(
    "/autotrade/signal/alarm/toggle",
    { alarm_id },
  )
  return res
}

export async function deleteSignalAlarm(alarm_id: string) {
  const res = await apiClient.post<SignalAlarmDeleteResponse>(
    "/autotrade/signal/alarm/delete",
    { alarm_id },
  )
  return res
} 