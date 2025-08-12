import { useState, useEffect, useCallback } from 'react';
import { useKoreaInvestApi } from './use-korea-invest-api';

export interface IndexTick {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string | null;
  last_updated: string | null;
  source: 'websocket' | 'rest' | 'cache' | 'unknown';
  status: 'active' | 'delayed' | 'closed' | 'error' | 'unknown';
  is_fresh: boolean;
}

export interface IndicesData {
  [symbol: string]: IndexTick;
}

export function useIndices() {
  const [indices, setIndices] = useState<IndicesData>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 한국투자증권 API 훅 사용
  const { hasApiKey, isLoading: apiLoading, error: apiError, getIndexData } = useKoreaInvestApi();

  // 지수 데이터 정의
  const indexDefinitions = [
    { symbol: 'KOSPI200', name: 'KOSPI 200', region: 'KR' as const },
    { symbol: 'KOSDAQ', name: 'KOSDAQ', region: 'KR' as const },
    { symbol: 'KRX100', name: 'KRX 100', region: 'KR' as const },
    { symbol: 'SPX', name: 'S&P 500', region: 'US' as const },
    { symbol: 'NASDAQ', name: 'NASDAQ', region: 'US' as const },
    { symbol: 'DJI', name: 'Dow Jones', region: 'US' as const },
    { symbol: 'RUT', name: 'Russell 2000', region: 'US' as const },
    { symbol: 'VIX', name: 'VIX', region: 'US' as const },
  ];

  // 실시간 데이터 가져오기
  const fetchIndicesData = useCallback(async () => {
    if (!hasApiKey) {
      console.log('API 키가 없어서 지수 데이터를 가져올 수 없습니다.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const newIndices: IndicesData = {};

      // 각 지수 데이터를 순차적으로 가져오기 (rate limit 방지)
      for (let i = 0; i < indexDefinitions.length; i++) {
        const indexDef = indexDefinitions[i];
        
        try {
          console.log(`${indexDef.symbol} 지수 데이터 조회 중... (${i + 1}/${indexDefinitions.length})`);
          
          const indexData = await getIndexData(indexDef.symbol, indexDef.region);
          
          newIndices[indexDef.symbol] = {
            symbol: indexDef.symbol,
            name: indexDef.name,
            price: indexData.value,
            change: indexData.change,
            change_pct: indexData.change_pct,
            volume: indexData.volume,
            timestamp: indexData.timestamp,
            last_updated: new Date().toISOString(),
            source: 'rest',
            status: 'active',
            is_fresh: true
          };

          // rate limit 방지를 위해 각 API 호출 사이에 1초 딜레이
          if (i < indexDefinitions.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        } catch (error) {
          console.error(`${indexDef.symbol} 지수 데이터 조회 실패:`, error);
          
          // 에러 시 기본 데이터 설정
          newIndices[indexDef.symbol] = {
            symbol: indexDef.symbol,
            name: indexDef.name,
            price: 0,
            change: 0,
            change_pct: 0,
            volume: 0,
            timestamp: null,
            last_updated: new Date().toISOString(),
            source: 'unknown',
            status: 'error',
            is_fresh: false
          };
        }
      }

      setIndices(newIndices);
      setIsConnected(true);
      console.log('지수 데이터를 성공적으로 가져왔습니다.');
    } catch (error) {
      console.error('지수 데이터 가져오기 실패:', error);
      setError('지수 데이터를 가져오는데 실패했습니다.');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [hasApiKey, getIndexData]);

  // 초기 데이터 로드
  useEffect(() => {
    if (hasApiKey && !apiLoading) {
      fetchIndicesData();
    }
  }, [hasApiKey, apiLoading, fetchIndicesData]);

  // 주기적 업데이트 (5분마다)
  useEffect(() => {
    if (!hasApiKey) return;

    const interval = setInterval(() => {
      console.log('지수 데이터 주기적 업데이트 시작...');
      fetchIndicesData();
    }, 5 * 60 * 1000); // 5분마다

    return () => clearInterval(interval);
  }, [hasApiKey, fetchIndicesData]);

  // 특정 인덱스 데이터 가져오기
  const getIndex = useCallback((symbol: string): IndexTick | null => {
    return indices[symbol] || null;
  }, [indices]);

  // 한국 지수들 가져오기
  const getKoreaIndices = useCallback((): IndexTick[] => {
    return Object.values(indices).filter(index => 
      ['KOSPI200', 'KOSDAQ', 'KRX100'].includes(index.symbol)
    );
  }, [indices]);

  // 미국 지수들 가져오기
  const getUSIndices = useCallback((): IndexTick[] => {
    return Object.values(indices).filter(index => 
      ['SPX', 'NASDAQ', 'DJI', 'RUT', 'VIX'].includes(index.symbol)
    );
  }, [indices]);

  // 환율 가져오기 (USD/KRW는 별도 처리 필요)
  const getFX = useCallback((): IndexTick | null => {
    // 환율은 별도 API 호출이 필요하므로 현재는 null 반환
    return null;
  }, []);

  // 활성 상태의 인덱스들만 가져오기
  const getActiveIndices = useCallback((): IndexTick[] => {
    return Object.values(indices).filter(index => index.status === 'active');
  }, [indices]);

  // 에러 상태의 인덱스들만 가져오기
  const getErrorIndices = useCallback((): IndexTick[] => {
    return Object.values(indices).filter(index => index.status === 'error');
  }, [indices]);

  // 수동 재연결
  const reconnect = useCallback(() => {
    console.log('지수 데이터 수동 재연결 시도...');
    fetchIndicesData();
  }, [fetchIndicesData]);

  return {
    // 상태
    indices,
    isConnected,
    error: error || apiError,
    isLoading: isLoading || apiLoading,
    
    // 데이터 접근 함수들
    getIndex,
    getKoreaIndices,
    getUSIndices,
    getFX,
    getActiveIndices,
    getErrorIndices,
    
    // 제어 함수들
    reconnect,
    fetchIndicesData
  };
} 