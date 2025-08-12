import { useState, useEffect, useRef, useCallback } from 'react';

interface StockData {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

interface IndexData {
  name: string;
  code: string;
  value: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

interface WebSocketData {
  stockData: Record<string, StockData>;
  indexData: Record<string, IndexData>;
}

export function useWebSocketStockData(
  onDataUpdate?: (data: WebSocketData) => void
) {
  const [isConnected, setIsConnected] = useState(false);
  const [stockData, setStockData] = useState<Record<string, StockData>>({});
  const [indexData, setIndexData] = useState<Record<string, IndexData>>({});
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(async () => {
    try {
      // 로컬 대시보드 모드: WebSocket 연결 비활성화
      console.log('로컬 대시보드 모드: WebSocket 연결 비활성화');
      setIsConnected(false);
      setError(null);
      return;
      
      // 아래 코드는 주석 처리
      // const accessToken = localStorage.getItem('accessToken') || localStorage.getItem('auth_token');
      // if (!accessToken) {
      //   throw new Error('인증 토큰이 없습니다. 로그인이 필요합니다.');
      // }
      // const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
      // const url = `${wsUrl}/api/dashboard/market/ws?token=${accessToken}`;
      // console.log('WebSocket 연결 시도:', url);
      // const ws = new WebSocket(url);
      // wsRef.current = ws;

      // ws.onopen = () => {
      //   console.log('WebSocket 연결됨');
      //   setIsConnected(true);
      //   setError(null);
      //   
      //   // 구독 메시지 전송
      //   const subscribeMessage = {
      //     type: 'subscribe',
      //     data: {
      //       indices: ['KOSPI', 'KOSDAQ', 'KOSPI200', 'S&P500', 'DOW', 'NASDAQ'],
      //       stocks: ['005930', '000660', '035420']
      //     }
      //   };
      //   ws.send(JSON.stringify(subscribeMessage));
      //   console.log('구독 메시지 전송:', subscribeMessage);
      // };

      // ws.onmessage = (event) => {
      //   try {
      //     const data = JSON.parse(event.data);
      //     console.log('WebSocket 메시지 수신:', data);

      //     if (data.type === 'market_update') {
      //       const newStockData = { ...stockData };
      //       const newIndexData = { ...indexData };

      //       // 주식 데이터 업데이트
      //       if (data.stocks) {
      //         data.stocks.forEach((stock: StockData) => {
      //           newStockData[stock.symbol] = stock;
      //         });
      //       }

      //       // 지수 데이터 업데이트
      //       if (data.indices) {
      //         data.indices.forEach((index: IndexData) => {
      //           newIndexData[index.code] = index;
      //         });
      //       }

      //       setStockData(newStockData);
      //       setIndexData(newIndexData);

      //       // 콜백 함수 호출 (MarketDataManager 업데이트용)
      //       if (onDataUpdate) {
      //         onDataUpdate({
      //           stockData: newStockData,
      //           indexData: newIndexData
      //       });
      //     }

      //     console.log('데이터 업데이트 완료:', {
      //       stocks: Object.keys(newStockData).length,
      //       indices: Object.keys(newIndexData).length
      //   });
      // }
      // } catch (error) {
      //   console.error('WebSocket 메시지 파싱 오류:', error);
      // }
      // };

      // ws.onclose = (event) => {
      //   console.log('WebSocket 연결 종료:', event.code, event.reason);
      //   setIsConnected(false);
      //   
      //   // 403 Forbidden이나 인증 오류가 아닌 경우에만 재연결 시도
      //   if (event.code !== 1008 && event.code !== 4003) {
      //     // 자동 재연결 (10초 후)
      //     if (reconnectTimeoutRef.current) {
      //       clearTimeout(reconnectTimeoutRef.current);
      //     }
      //     reconnectTimeoutRef.current = setTimeout(() => {
      //       console.log('WebSocket 재연결 시도...');
      //       connect();
      //     }, 10000);
      //   } else {
      //     console.log('인증 오류로 인한 연결 종료. 재연결을 시도하지 않습니다.');
      //     setError('인증이 필요합니다. 다시 로그인해주세요.');
      //   }
      // };

      // ws.onerror = (error) => {
      //   console.error('WebSocket 오류:', error);
      //   setError('WebSocket 연결 오류가 발생했습니다. 백엔드 서버가 실행 중인지 확인해주세요.');
      // };

    } catch (error) {
      console.error('WebSocket 연결 실패:', error);
      setError(error instanceof Error ? error.message : '연결 실패');
    }
  }, [stockData, indexData, onDataUpdate]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const getWsStockData = useCallback((symbol: string): StockData | null => {
    return stockData[symbol] || null;
  }, [stockData]);

  const getWsIndexData = useCallback((code: string): IndexData | null => {
    return indexData[code] || null;
  }, [indexData]);

  const getAllWsData = useCallback(() => ({ stockData, indexData }), [stockData, indexData]);

  return {
    isConnected,
    stockData,
    indexData,
    error,
    getWsStockData,
    getWsIndexData,
    getAllWsData,
    reconnect: connect
  };
} 