"use client"

import { useState, useCallback } from "react"
import { apiClient } from "@/lib/api/client"
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

export interface AutoTradeError {
  code: number
  message: string
  details?: string
}

export function useAutoTrade() {
  const [strategies, setStrategies] = useState<AutoTradeStrategy[]>([])
  const [currentStrategy, setCurrentStrategy] = useState<AutoTradeStrategy | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<AutoTradeError | null>(null)

  // 전략 목록 불러오기
  const loadStrategies = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiClient.get("/api/autotrade/strategies") as any
      
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
      // 공통 에러 처리 사용
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        // 세션 만료 시 에러 상태만 설정 (리다이렉트는 자동 처리됨)
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
      const response = await apiClient.post("/api/autotrade/strategies", strategyData) as any
      
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
        return { success: false, error: "세션이 만료되었습니다" }
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
      const response = await apiClient.put(`/api/autotrade/strategies/${strategyId}/toggle`, { isActive }) as any
      
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
        return { success: false, error: "세션이 만료되었습니다" }
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
      const response = await apiClient.post(`/api/autotrade/strategies/${strategyId}/backtest`, parameters) as any
      
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
        return { success: false, error: "세션이 만료되었습니다" }
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
      const response = await apiClient.delete(`/api/autotrade/strategies/${strategyId}`) as any
      
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
        return { success: false, error: "세션이 만료되었습니다" }
      }
      
      setError({
        code: errorInfo.errorCode || -1,
        message: errorInfo.message,
        details: e.message || "네트워크 오류"
      })
      return { success: false, error: errorInfo.message }
    }
  }, [currentStrategy])

  // 에러 초기화
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    strategies,
    currentStrategy,
    isLoading,
    error,
    loadStrategies,
    createStrategy,
    toggleStrategy,
    runBacktest,
    deleteStrategy,
    clearError,
    setCurrentStrategy
  }
} 