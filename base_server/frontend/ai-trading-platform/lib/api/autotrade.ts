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

export interface SignalHistoryResponse {
  errorCode: number
  signals?: any[]
  total_count?: number
  message?: string
}

export interface YahooSearchResponse {
  errorCode: number
  results?: any[]
  total_count?: number
  message?: string
}

export interface YahooDetailResponse {
  errorCode: number
  detail?: any
  message?: string
}

// 시그널 알림 관련 API
export async function createSignalAlarm(params: { symbol: string; note?: string }) {
  const res = await apiClient.post<SignalAlarmCreateResponse>(
    "/api/autotrade/signal/alarm/create",
    params,
  )
  return res
}

export async function listSignalAlarms() {
  const res = await apiClient.post<SignalAlarmListResponse>(
    "/api/autotrade/signal/alarm/list",
    {},
  )
  return res
}

export async function toggleSignalAlarm(alarm_id: string) {
  const res = await apiClient.post<SignalAlarmToggleResponse>(
    "/api/autotrade/signal/alarm/toggle",
    { alarm_id },
  )
  return res
}

export async function deleteSignalAlarm(alarm_id: string) {
  const res = await apiClient.post<SignalAlarmDeleteResponse>(
    "/api/autotrade/signal/alarm/delete",
    { alarm_id },
  )
  return res
}

export async function getSignalHistory(params: { page?: number; limit?: number }) {
  const res = await apiClient.post<SignalHistoryResponse>(
    "/api/autotrade/signal/history",
    params,
  )
  return res
}

// 야후 파이낸스 관련 API
export async function searchYahooStocks(params: { query: string; limit?: number }) {
  const res = await apiClient.post<YahooSearchResponse>(
    "/api/autotrade/yahoo/search",
    params,
  )
  return res
}

export async function getYahooStockDetail(params: { symbol: string }) {
  const res = await apiClient.post<YahooDetailResponse>(
    "/api/autotrade/yahoo/detail",
    params,
  )
  return res
}

// autotradeService 객체로 export
export const autotradeService = {
  // 시그널 알림
  createSignalAlarm,
  listSignalAlarms,
  toggleSignalAlarm,
  deleteSignalAlarm,
  getSignalHistory,
  
  // 야후 파이낸스
  searchYahooStocks,
  getYahooStockDetail,
  
  // 전략 관련 (기존 호환성을 위해 추가)
  listStrategies: async () => {
    // 기존 전략 목록 API가 없으므로 빈 배열 반환
    return { errorCode: 0, strategies: [] };
  },
  
  createStrategy: async (strategyData: any) => {
    // 기존 전략 생성 API가 없으므로 에러 반환
    return { errorCode: 1001, message: "전략 생성 API가 구현되지 않았습니다." };
  },
  
  toggleStrategy: async (strategyId: string, isActive: boolean) => {
    // 기존 전략 토글 API가 없으므로 에러 반환
    return { errorCode: 1001, message: "전략 토글 API가 구현되지 않았습니다." };
  },
  
  runBacktest: async (strategyId: string, parameters: any) => {
    // 기존 백테스트 API가 없으므로 에러 반환
    return { errorCode: 1001, message: "백테스트 API가 구현되지 않았습니다." };
  },
  
  deleteStrategy: async (strategyId: string) => {
    // 기존 전략 삭제 API가 없으므로 에러 반환
    return { errorCode: 1001, message: "전략 삭제 API가 구현되지 않았습니다." };
  }
}; 