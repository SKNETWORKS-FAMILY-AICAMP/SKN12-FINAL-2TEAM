import React, { useState, useEffect, useMemo, useRef } from "react";
import { useNasdaqStocks } from '@/hooks/use-nasdaq-stocks';

type RecItem = { date: string; ticker: string; reason: string; report: string; };
type RecItemWithColor = RecItem & { color?: string };

const TICKER_NAME: Record<string, string> = {
  AAPL: "Apple Inc.", MSFT: "Microsoft", GOOGL: "Alphabet",
  TSLA: "Tesla", NVDA: "NVIDIA", AMZN: "Amazon",
};

function hexToRgba(hex: string, alpha = 0.1): string {
  try {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!m) return "rgba(31,41,55,0.1)"; // fallback to #1f2937
    const r = parseInt(m[1], 16);
    const g = parseInt(m[2], 16);
    const b = parseInt(m[3], 16);
    const a = Math.min(Math.max(alpha, 0), 1);
    return `rgba(${r}, ${g}, ${b}, ${a})`;
  } catch {
    return "rgba(31,41,55,0.1)";
  }
}

function Sparkline({ data, color = "#60a5fa" }: { data: number[]; color?: string }) {
  const width = 160, height = 80;
  const min = Math.min(...data), max = Math.max(...data);
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / (max - min || 1)) * height;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={width} height={height} style={{ minWidth: width }}>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="4"
        points={points}
      />
    </svg>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-xl border-0 bg-white/60 dark:bg-[#18181c]/60 backdrop-blur-xl shadow-md p-4 flex flex-col items-start min-h-[320px] min-w-[280px] w-full animate-pulse">
      <div className="flex items-center w-full mb-3">
        <div className="w-12 h-12 rounded-full bg-gray-300/60 dark:bg-gray-700/60 mr-5" />
        <div className="flex-1">
          <div className="h-5 w-40 bg-gray-300/60 dark:bg-gray-700/60 rounded mb-2" />
          <div className="h-4 w-24 bg-gray-300/60 dark:bg-gray-700/60 rounded" />
        </div>
      </div>
      <div className="flex items-center justify-between w-full mb-3">
        <div className="h-7 w-24 bg-gray-300/60 dark:bg-gray-700/60 rounded" />
      </div>
      <div className="mt-auto w-full pt-2">
        <div className="h-4 w-20 bg-gray-300/60 dark:bg-gray-700/60 rounded mb-2" />
        <div className="space-y-2">
          <div className="h-3 w-full bg-gray-300/60 dark:bg-gray-700/60 rounded" />
          <div className="h-3 w-11/12 bg-gray-300/60 dark:bg-gray-700/60 rounded" />
          <div className="h-3 w-10/12 bg-gray-300/60 dark:bg-gray-700/60 rounded" />
        </div>
      </div>
      {/* 서버 환경을 위한 로딩 메시지 추가 */}
      <div className="mt-4 text-center w-full">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          AI 추천 종목 분석 중... (최대 120초)
        </div>
        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
          서버 환경에서는 응답이 늦을 수 있습니다
        </div>
      </div>
    </div>
  );
}

export default function RecommendStocksCards() {
  const [items, setItems] = useState<RecItemWithColor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [openIdx, setOpenIdx] = useState<number | null>(null);
  const [tick, setTick] = useState(0);
  const { initWs, addSymbol, getStock, subscribeStore, requestPrices } = useNasdaqStocks();

  // 추천 데이터 로드 (초기 1회)
  useEffect(() => {
    void initWs();
    const unsub = subscribeStore(() => setTick((v) => v + 1));
    return () => { if (typeof unsub === 'function') unsub(); };
  }, [initWs, subscribeStore]);

  // 추천 데이터 로드 (초기 1회, StrictMode 중복 실행 가드)
  useEffect(() => {
    // 이미 데이터가 있으면 실행하지 않음
    if (items.length > 0) return;
    
    let isMounted = true;
    const loadRecommendations = async () => {
      try {
        setIsLoading(true);
        const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;
        if (!accessToken) {
          setIsLoading(false);
          return;
        }
        
        // 서버 환경을 위한 긴 타임아웃 설정
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 120초 타임아웃
        
        console.log("🚀 [RecommendStocks] API 호출 시작...");
        const res = await fetch('/api/dashboard/stock/recommendation', {
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ accessToken, market: 'NASDAQ', strategy: 'MOMENTUM' }),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!res.ok) {
          console.error("❌ [RecommendStocks] API 응답 실패:", res.status);
          if (isMounted) setIsLoading(false);
          return;
        }
        
        let data = await res.json();
        
        // 문자열로 온 경우 파싱
        if (typeof data === 'string') {
          console.log("🔍 [RecommendStocks] 응답이 문자열로 옴, JSON 파싱 시도");
          try {
            data = JSON.parse(data);
          } catch (parseError) {
            console.error("❌ [RecommendStocks] JSON 파싱 실패:", parseError);
            if (isMounted) setIsLoading(false);
            return;
          }
        }
        
        // 디버깅을 위한 로그 추가
        console.log("🔍 [RecommendStocksCards] 백엔드 응답:", data);
        console.log("🔍 [RecommendStocksCards] 응답 타입:", typeof data);
        console.log("🔍 [RecommendStocksCards] recommendations 키 존재:", data && typeof data === 'object' ? 'recommendations' in data : false);
        
        // 백엔드가 recommendations 배열로 내려줌 - 강화된 파싱
        let recommendations = [];
        
        console.log("🔍 [RecommendStocks] 원본 데이터 상세 분석:");
        console.log("- 타입:", typeof data);
        console.log("- 값:", data);
        console.log("- 키들:", Object.keys(data || {}));
        
        if (data && typeof data === 'object') {
          // 1. 직접 recommendations 키가 있는 경우
          if (data.recommendations && Array.isArray(data.recommendations)) {
            recommendations = data.recommendations;
            console.log("✅ [RecommendStocks] 직접 recommendations 배열 발견:", recommendations.length);
          }
          // 2. errorCode가 0이고 result가 success인 경우 강제로 확인
          else if (data.errorCode === 0 && data.result === "success") {
            console.log("🔍 [RecommendStocks] 성공 응답이지만 recommendations 누락, 전체 객체 확인");
            console.log("- 모든 속성:", JSON.stringify(data, null, 2));
            
            // 혹시 다른 키에 배열이 있는지 확인
            for (const [key, value] of Object.entries(data)) {
              if (Array.isArray(value) && value.length > 0) {
                console.log(`🔍 [RecommendStocks] 배열 발견: ${key}`, value);
                if (key === 'recommendations' || value.some(item => item.ticker)) {
                  recommendations = value;
                  console.log(`✅ [RecommendStocks] ${key} 배열을 recommendations로 사용`);
                  break;
                }
              }
            }
          }
        }
        
        // 3. 여전히 빈 배열이면 강제로 기본 데이터 생성 (디버깅용)
        if (recommendations.length === 0 && data && data.errorCode === 0) {
          console.log("🚨 [RecommendStocks] 응답은 성공했지만 추천 데이터가 없음, 기본 데이터 생성");
          recommendations = [
            {
              date: "2025-08-21",
              ticker: "DEBUG",
              reason: "디버깅용 더미 데이터 - 실제 응답 파싱 실패",
              report: `원본 응답: ${JSON.stringify(data)}`,
              color: "#ff0000"
            }
          ];
        }
        
        console.log("🔍 [RecommendStocksCards] 파싱된 recommendations:", recommendations);
        
        const arr: RecItemWithColor[] = recommendations.map((x: any) => ({
          date: String(x.date ?? ''),
          ticker: String(x.ticker ?? ''),
          reason: String(x.reason ?? ''),
          report: String(x.report ?? ''),
          color: typeof x.color === 'string' ? x.color : undefined,
        }));
        
        console.log("🔍 [RecommendStocksCards] 최종 변환된 배열:", arr);
        console.log("🔍 [RecommendStocksCards] 배열 길이:", arr.length);
        console.log("🔍 [RecommendStocksCards] 첫 번째 아이템:", arr[0]);
        
        // 컴포넌트가 여전히 마운트되어 있는지 확인
        if (!isMounted) {
          console.log("❌ [RecommendStocks] 컴포넌트가 언마운트됨, 상태 업데이트 취소");
          return;
        }
        
        // 상태 업데이트를 강제로 처리
        console.log("🔄 [RecommendStocks] 상태 업데이트 시작...");
        setItems(arr);
        setIsLoading(false); // 명시적으로 로딩 완료 처리
        
        // 상태 업데이트 확인을 위한 지연
        setTimeout(() => {
          console.log("✅ [RecommendStocks] items 상태 업데이트 완료, 길이:", arr.length);
          console.log("✅ [RecommendStocks] 현재 isLoading:", false);
        }, 100);
        
        // 추천 종목 실시간 구독 + 초기 REST 가격 큐 등록(전역 큐가 0.5초 간격 직렬 처리)
        for (const it of arr) {
          addSymbol(it.ticker);
        }
        requestPrices(arr.map((x) => x.ticker));
      } catch (e) {
        console.error('❌ [RecommendStocks] API 호출 에러:', e);
        
        if (isMounted) {
          if (e instanceof Error && e.name === 'AbortError') {
            console.log('⏰ [RecommendStocks] 요청 타임아웃 - 서버 응답이 너무 늦습니다');
          }
          
          // 에러 발생 시에도 로딩 상태 해제
          setIsLoading(false);
          console.log("🔄 [RecommendStocks] 에러로 인한 로딩 상태 해제");
        }
      } finally {
        console.log("🔚 [RecommendStocks] API 호출 완료");
      }
    };
    
    // 비동기 함수 실행
    loadRecommendations();
    
    // 클린업 함수
    return () => {
      isMounted = false;
    };
  }, [items.length, addSymbol, requestPrices]);

  const modalItem = openIdx !== null ? items[openIdx] : null;
  const prices = useMemo(() => {
    const out: Record<string, number> = {};
    for (const it of items) {
      const sd = getStock(it.ticker);
      if (sd?.price) out[it.ticker] = sd.price;
    }
    return out;
  }, [items, getStock, tick]);

  // 디버깅을 위한 렌더링 상태 확인
  console.log("🖼️ [RecommendStocks] 렌더링 상태:", {
    isLoading,
    itemsLength: items.length,
    items: items.map(it => ({ ticker: it.ticker, reason: it.reason?.substring(0, 30) }))
  });

  return (
    <div className="w-full max-w-7xl bg-gradient-to-br from-black via-gray-900 to-gray-850 rounded-2xl shadow-2xl border border-gray-800 p-4 flex flex-col gap-4">
      {/* 디버깅 정보 표시 */}
      <div className="text-xs text-gray-500 mb-2">
        Debug: Loading={isLoading ? 'true' : 'false'}, Items={items.length}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
        {(() => {
          console.log("🎨 [RecommendStocks] 렌더링 조건 체크:", {
            itemsLength: items.length,
            isLoadingState: isLoading,
            shouldShowSkeleton: items.length === 0
          });
          
          if (items.length === 0) {
            return Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={`skeleton-${i}`} />
            ));
          }
          
          console.log("🎨 [RecommendStocks] 실제 카드 렌더링 시작, 개수:", items.length);
          
          return items.map((it, i) => {
            const name = TICKER_NAME[it.ticker] ?? it.ticker;
            const price = prices[it.ticker];
            const sd = getStock(it.ticker);
            const delta = sd?.change ?? 0;
            const pct = sd?.changePct ?? 0;
            const isUp = Number.isFinite(delta) ? delta >= 0 : true;
            const dirColor = isUp ? '#ef4444' : '#3b82f6';
            const cardColor = (typeof it.color === 'string' && /^#([0-9A-Fa-f]{6})$/.test(it.color)) ? it.color : '#1f2937';
            const headerBg = hexToRgba(cardColor, 0.1);
            
            console.log(`🎨 [RecommendStocks] 카드 ${i+1} 렌더링:`, {
              ticker: it.ticker,
              name,
              cardColor,
              reason: it.reason?.substring(0, 30)
            });
            
            return (
              <button
                key={`rec-card-${it.ticker}-${i}`}
                onClick={() => setOpenIdx(i)}
                className="group text-left rounded-xl border-0 backdrop-blur-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 shadow-md p-4 flex flex-col items-start min-h-[320px] min-w-[280px] w-full"
                style={{ 
                  background: '#0b0b0e', 
                  borderColor: cardColor, 
                  borderWidth: 1,
                  display: 'flex' // 강제로 표시
                }}
              >
                <div className="flex items-center w-full mb-3" style={{ background: headerBg, borderRadius: 12, padding: 8 }}>
                  <div className="w-12 h-12 rounded-full text-black font-bold text-xl flex items-center justify-center mr-5 shadow" style={{ background: cardColor }}>
                    {it.ticker.substring(0,1)}
                  </div>
                  <div className="flex-1">
                    <div className="text-xl font-bold leading-tight" style={{ color: cardColor }}>{name}</div>
                    <div className="text-sm text-gray-400 font-semibold">{it.ticker}</div>
                  </div>
                </div>
                <div className="flex items-center justify-between w-full mb-3">
                  <div className="flex items-center">
                    <span className="text-2xl font-extrabold mr-3" style={{ color: dirColor }}>{price ? price.toLocaleString() : '-'}</span>
                    {sd && (
                      <span className="text-sm font-bold" style={{ color: dirColor }}>
                        {isUp ? '▲' : '▼'} {delta >= 0 ? '+' : ''}{delta.toLocaleString()} ({pct >= 0 ? '+' : ''}{Number.isFinite(pct) ? pct.toFixed(2) : '0.00'}%)
                      </span>
                    )}
                  </div>
                </div>
                <div className="mt-auto w-full pt-2">
                  <div className="text-sm text-gray-400 mb-1 font-semibold">추천 사유</div>
                  <div className="text-sm text-gray-300 line-clamp-3 whitespace-pre-line leading-relaxed">
                    {it.reason || '-'}
                  </div>
                </div>
              </button>
            );
          });
        })()}
      </div>

      {modalItem && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
          onClick={() => setOpenIdx(null)}
        >
          <div
            className="bg-[#111114] text-white max-w-2xl w-[92%] md:w-[720px] rounded-xl p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="text-lg text-gray-400">{modalItem.date}</div>
                <div className="text-2xl font-bold">{modalItem.ticker}</div>
              </div>
              <button onClick={() => setOpenIdx(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            <div className="mb-4">
              <div className="text-sm text-gray-400 mb-1">추천 사유</div>
              <div className="whitespace-pre-line leading-relaxed">{modalItem.reason || '-'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">레포트</div>
              <div className="whitespace-pre-line leading-relaxed">{modalItem.report || '-'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
