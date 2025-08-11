"use client"

import { useState, useCallback } from "react"
import { autotradeService } from "@/lib/api/autotrade"
import { handleApiError, getErrorMessage } from "@/lib/error-handler"

export interface AutoTradeStrategy {
  id: string
  name: string
  description: string
  isActive: boolean
  parameters: Record<string, any>
  createdAt: string
  updatedAt: string
}

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

export interface AutoTradeError {
  code: number
  message: string
  details?: string
}

export function useAutoTrade() {
  const [strategies, setStrategies] = useState<AutoTradeStrategy[]>([])
  const [currentStrategy, setCurrentStrategy] = useState<AutoTradeStrategy | null>(null)
  const [signalAlarms, setSignalAlarms] = useState<SignalAlarmInfo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<AutoTradeError | null>(null)

  // 전략 목록 불러오기
  const loadStrategies = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await autotradeService.listStrategies() as any
      
      if (response.errorCode === 0) {
        setStrategies(response.strategies || [])
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError({
          code: 10000,
          message: errorInfo.message,
          details: "세션이 만료되어 로그인 페이지로 이동합니다."
        })
        return
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      console.error("전략 목록 불러오기 실패:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 전략 생성
  const createStrategy = useCallback(async (strategyData: Partial<AutoTradeStrategy>) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await autotradeService.createStrategy(strategyData) as any
      
      if (response.errorCode === 0) {
        const newStrategy = response.strategy
        setStrategies(prev => [newStrategy, ...prev])
        setCurrentStrategy(newStrategy)
        return { success: true, strategy: newStrategy }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError({
          code: 10000,
          message: errorInfo.message,
          details: "세션이 만료되어 로그인 페이지로 이동합니다."
        })
        return { success: false, error: "세션 만료" }
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 전략 활성화/비활성화
  const toggleStrategy = useCallback(async (strategyId: string, isActive: boolean) => {
    try {
      const response = await autotradeService.toggleStrategy(strategyId, isActive) as any
      
      if (response.errorCode === 0) {
        setStrategies(prev => prev.map(strategy => 
          strategy.id === strategyId 
            ? { ...strategy, isActive, updatedAt: new Date().toISOString() }
            : strategy
        ))
        return { success: true }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError({
          code: 10000,
          message: errorInfo.message,
          details: "세션이 만료되어 로그인 페이지로 이동합니다."
        })
        return { success: false, error: "세션 만료" }
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    }
  }, [])

  // 백테스트 실행
  const runBacktest = useCallback(async (strategyId: string, parameters: Record<string, any>) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await autotradeService.runBacktest(strategyId, parameters) as any
      
      if (response.errorCode === 0) {
        return { success: true, results: response.results }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError({
          code: 10000,
          message: errorInfo.message,
          details: "세션이 만료되어 로그인 페이지로 이동합니다."
        })
        return { success: false, error: "세션 만료" }
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 전략 삭제
  const deleteStrategy = useCallback(async (strategyId: string) => {
    try {
      const response = await autotradeService.deleteStrategy(strategyId) as any
      
      if (response.errorCode === 0) {
        setStrategies(prev => prev.filter(strategy => strategy.id !== strategyId))
        if (currentStrategy?.id === strategyId) {
          setCurrentStrategy(null)
        }
        return { success: true }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError({
          code: 10000,
          message: errorInfo.message,
          details: "세션이 만료되어 로그인 페이지로 이동합니다."
        })
        return { success: false, error: "세션 만료" }
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    }
  }, [currentStrategy])

  // 시그널 알림 목록 불러오기
  const loadSignalAlarms = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await autotradeService.listSignalAlarms() as any
      
      if (response.errorCode === 0) {
        setSignalAlarms(response.alarms || [])
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError({
          code: 10000,
          message: errorInfo.message,
          details: "세션이 만료되어 로그인 페이지로 이동합니다."
        })
        return
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      console.error("시그널 알림 목록 불러오기 실패:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 시그널 알림 생성
  const createSignalAlarm = useCallback(async (symbol: string, note?: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await autotradeService.createSignalAlarm({ symbol, note }) as any
      
      if (response.errorCode === 0) {
        const newAlarm = response.alarm_info
        if (newAlarm) {
          setSignalAlarms(prev => [newAlarm, ...prev])
        }
        return { success: true, alarm: newAlarm }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError({
          code: 10000,
          message: errorInfo.message,
          details: "세션이 만료되어 로그인 페이지로 이동합니다."
        })
        return { success: false, error: "세션 만료" }
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 시그널 알림 토글
  const toggleSignalAlarm = useCallback(async (alarm_id: string) => {
    try {
      const response = await autotradeService.toggleSignalAlarm(alarm_id) as any
      
      if (response.errorCode === 0) {
        setSignalAlarms(prev => prev.map(alarm => 
          alarm.alarm_id === alarm_id 
            ? { ...alarm, is_active: response.is_active || !alarm.is_active }
            : alarm
        ))
        return { success: true }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    }
  }, [])

  // 시그널 알림 삭제
  const deleteSignalAlarm = useCallback(async (alarm_id: string) => {
    try {
      const response = await autotradeService.deleteSignalAlarm(alarm_id) as any
      
      if (response.errorCode === 0) {
        setSignalAlarms(prev => prev.filter(alarm => alarm.alarm_id !== alarm_id))
        return { success: true }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    }
  }, [])

  // 야후 주식 검색
  const searchYahooStocks = useCallback(async (query: string, limit: number = 10) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await autotradeService.searchYahooStocks({ query, limit }) as any
      
      if (response.errorCode === 0) {
        return { success: true, results: response.results || [] }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 야후 주식 상세 정보
  const getYahooStockDetail = useCallback(async (symbol: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await autotradeService.getYahooStockDetail({ symbol }) as any
      
      if (response.errorCode === 0) {
        return { success: true, detail: response.detail }
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError({
          code: response.errorCode,
          message: errorMessage,
          details: response.message
        })
        return { success: false, error: errorMessage }
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 에러 초기화
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    // 상태
    strategies,
    currentStrategy,
    signalAlarms,
    isLoading,
    error,
    
    // 전략 관련
    loadStrategies,
    createStrategy,
    toggleStrategy,
    runBacktest,
    deleteStrategy,
    
    // 시그널 알림 관련
    loadSignalAlarms,
    createSignalAlarm,
    toggleSignalAlarm,
    deleteSignalAlarm,
    
    // 야후 파이낸스 관련
    searchYahooStocks,
    getYahooStockDetail,
    
    // 기타
    clearError,
    
    // 설정 함수
    setCurrentStrategy
  };
} 