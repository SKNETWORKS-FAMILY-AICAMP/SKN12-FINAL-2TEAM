// Yahoo Finance API 프록시 (백엔드 통신)
// CORS, 속도 제한, 법적 문제 등을 해결하기 위해 백엔드 프록시 사용

/**
 * 주식 검색 API - 백엔드 프록시 사용
 * @param query 검색할 기업명 또는 심볼
 * @returns 검색 결과
 */
export async function searchStocks(query: string) {
  try {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(`/api/autotrade/yahoo/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ query, ...(token ? { accessToken: token } : {}) })
    });
    const data = await response.json();
    // errorCode만 체크
    if (data?.errorCode === 0 && data?.securities) {
      return data;
    } else {
      throw new Error(data?.message || '검색 실패');
    }
  } catch (err) {
    throw err;
  }
}

/**
 * 주식 상세 정보 API - 백엔드 프록시 사용
 * @param symbol 주식 심볼
 * @returns 주식 상세 정보
 */
export async function getStockDetail(symbol: string) {
  try {
    // symbol 유효성 검사
    if (!symbol || typeof symbol !== 'string' || !symbol.trim()) {
      throw new Error(`유효하지 않은 symbol: ${symbol}`);
    }
    
    // symbol이 string인지 확인하고 변환
    const symbolStr = typeof symbol === 'string' ? symbol : String(symbol);
    
    const token = localStorage.getItem('accessToken');
    const response = await fetch(`/api/autotrade/yahoo/detail/${encodeURIComponent(symbolStr)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ ...(token ? { accessToken: token } : {}) })
    });
    const data = await response.json();
    if (data?.errorCode === 0) {
      return data;
    } else {
      throw new Error(data?.message || '상세 정보 조회 실패');
    }
  } catch (err) {
    throw err;
  }
}





 