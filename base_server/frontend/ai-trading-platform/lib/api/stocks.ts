// Yahoo Finance API 프록시 (백엔드 통신)
// CORS, 속도 제한, 법적 문제 등을 해결하기 위해 백엔드 프록시 사용

import { apiClient } from "@/lib/api/client"

/**
 * 주식 검색 API - 백엔드 프록시 사용
 * @param query 검색할 기업명 또는 심볼
 * @returns 검색 결과
 */
export async function searchStocks(query: string) {
  const data = await apiClient.post<any>("/api/autotrade/yahoo/search", { query })
  return data
}

/**
 * 주식 상세 정보 API - 백엔드 프록시 사용
 * @param symbol 주식 심볼
 * @returns 주식 상세 정보
 */
export async function getStockDetail(symbol: string) {
  if (!symbol || typeof symbol !== "string" || !symbol.trim()) {
    throw new Error(`유효하지 않은 symbol: ${symbol}`)
  }
  const data = await apiClient.post<any>("/api/autotrade/yahoo/detail", { symbol })
  return data
}





 