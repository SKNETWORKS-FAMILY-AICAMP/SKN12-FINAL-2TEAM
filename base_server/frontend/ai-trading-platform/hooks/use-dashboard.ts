"use client"

import { useState, useCallback, useEffect } from "react"
import { apiClient } from "@/lib/api/client"
import { handleApiError, getErrorMessage } from "@/lib/error-handler"

export interface DashboardData {
  portfolioValue: number
  totalReturn: number
  dailyReturn: number
  activePositions: number
  recentTrades: Array<{
    id: string
    symbol: string
    type: "buy" | "sell"
    quantity: number
    price: number
    timestamp: string
  }>
  marketOverview: {
    kospi: { value: number; change: number }
    kosdaq: { value: number; change: number }
    usd: { value: number; change: number }
  }
  alerts: Array<{
    id: string
    type: "info" | "warning" | "error"
    message: string
    timestamp: string
  }>
}

export interface DashboardError {
  code: number
  message: string
  details?: string
}

export function useDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<DashboardError | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // 대시보드 데이터 로드
  const loadDashboardData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiClient.get("/api/dashboard") as any
      
      if (response.errorCode === 0) {
        setDashboardData(response.data)
        setLastUpdated(new Date())
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
      console.error("대시보드 데이터 로드 실패:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 포트폴리오 요약 데이터만 로드
  const loadPortfolioSummary = useCallback(async () => {
    try {
      const response = await apiClient.get("/api/dashboard/portfolio-summary") as any
      
      if (response.errorCode === 0) {
        setDashboardData(prev => prev ? {
          ...prev,
          portfolioValue: response.data.portfolioValue,
          totalReturn: response.data.totalReturn,
          dailyReturn: response.data.dailyReturn,
          activePositions: response.data.activePositions
        } : null)
        setLastUpdated(new Date())
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

  // 시장 데이터만 로드
  const loadMarketData = useCallback(async () => {
    try {
      const response = await apiClient.get("/api/dashboard/market-data") as any
      
      if (response.errorCode === 0) {
        setDashboardData(prev => prev ? {
          ...prev,
          marketOverview: response.data.marketOverview
        } : null)
        setLastUpdated(new Date())
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

  // 최근 거래 내역만 로드
  const loadRecentTrades = useCallback(async () => {
    try {
      const response = await apiClient.get("/api/dashboard/recent-trades") as any
      
      if (response.errorCode === 0) {
        setDashboardData(prev => prev ? {
          ...prev,
          recentTrades: response.data.recentTrades
        } : null)
        setLastUpdated(new Date())
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

  // 알림 데이터만 로드
  const loadAlerts = useCallback(async () => {
    try {
      const response = await apiClient.get("/api/dashboard/alerts") as any
      
      if (response.errorCode === 0) {
        setDashboardData(prev => prev ? {
          ...prev,
          alerts: response.data.alerts
        } : null)
        setLastUpdated(new Date())
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

  // 에러 초기화
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // 컴포넌트 마운트 시 대시보드 데이터 로드
  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  return {
    dashboardData,
    isLoading,
    error,
    lastUpdated,
    loadDashboardData,
    loadPortfolioSummary,
    loadMarketData,
    loadRecentTrades,
    loadAlerts,
    clearError
  }
} 