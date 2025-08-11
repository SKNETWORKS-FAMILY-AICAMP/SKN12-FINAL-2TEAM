"use client"

import { useState, useCallback, useEffect } from "react"
import { apiClient } from "@/lib/api/client"
import { handleApiError, getErrorMessage } from "@/lib/error-handler"

export interface PortfolioPosition {
  id: string
  symbol: string
  name: string
  quantity: number
  averagePrice: number
  currentPrice: number
  marketValue: number
  unrealizedPnL: number
  unrealizedPnLPercent: number
  sector: string
  lastUpdated: string
}

export interface PortfolioSummary {
  totalValue: number
  totalCost: number
  totalUnrealizedPnL: number
  totalUnrealizedPnLPercent: number
  cashBalance: number
  marginUsed: number
  availableMargin: number
  lastUpdated: string
}

export interface PortfolioError {
  code: number
  message: string
  details?: string
}

export function usePortfolio() {
  const [positions, setPositions] = useState<PortfolioPosition[]>([])
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<PortfolioError | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // 포트폴리오 요약 정보 로드
  const loadPortfolioSummary = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiClient.get("/api/portfolio/summary") as any
      
      if (response.errorCode === 0) {
        setSummary(response.data)
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
      console.error("포트폴리오 요약 로드 실패:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 포지션 목록 로드
  const loadPositions = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiClient.get("/api/portfolio/positions") as any
      
      if (response.errorCode === 0) {
        setPositions(response.positions || [])
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
      console.error("포지션 목록 로드 실패:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 주식 매수
  const buyStock = useCallback(async (symbol: string, quantity: number, price?: number) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const orderData = {
        symbol,
        quantity,
        orderType: price ? "limit" : "market",
        price: price || undefined
      }
      
      const response = await apiClient.post("/api/portfolio/buy", orderData) as any
      
      if (response.errorCode === 0) {
        // 성공 시 포트폴리오 새로고침
        await Promise.all([loadPortfolioSummary(), loadPositions()])
        return { success: true, orderId: response.orderId }
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
  }, [loadPortfolioSummary, loadPositions])

  // 주식 매도
  const sellStock = useCallback(async (symbol: string, quantity: number, price?: number) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const orderData = {
        symbol,
        quantity,
        orderType: price ? "limit" : "market",
        price: price || undefined
      }
      
      const response = await apiClient.post("/api/portfolio/sell", orderData) as any
      
      if (response.errorCode === 0) {
        // 성공 시 포트폴리오 새로고침
        await Promise.all([loadPortfolioSummary(), loadPositions()])
        return { success: true, orderId: response.orderId }
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
  }, [loadPortfolioSummary, loadPositions])

  // 포지션 상세 정보 로드
  const loadPositionDetails = useCallback(async (symbol: string) => {
    try {
      const response = await apiClient.get(`/api/portfolio/positions/${symbol}`) as any
      
      if (response.errorCode === 0) {
        return { success: true, position: response.position }
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

  // 포트폴리오 전체 새로고침
  const refreshPortfolio = useCallback(async () => {
    await Promise.all([loadPortfolioSummary(), loadPositions()])
  }, [loadPortfolioSummary, loadPositions])

  // 에러 초기화
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // 컴포넌트 마운트 시 포트폴리오 데이터 로드
  useEffect(() => {
    refreshPortfolio()
  }, [refreshPortfolio])

  return {
    positions,
    summary,
    isLoading,
    error,
    lastUpdated,
    loadPortfolioSummary,
    loadPositions,
    buyStock,
    sellStock,
    loadPositionDetails,
    refreshPortfolio,
    clearError
  }
} 