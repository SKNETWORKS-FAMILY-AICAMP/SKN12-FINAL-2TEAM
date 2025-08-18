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
    </div>
  );
}

export default function RecommendStocksCards() {
  const [items, setItems] = useState<RecItemWithColor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [openIdx, setOpenIdx] = useState<number | null>(null);
  const [tick, setTick] = useState(0);
  const { initWs, addSymbol, getStock, subscribeStore, requestPrices } = useNasdaqStocks();
  const fetchedRef = useRef(false);

  // 추천 데이터 로드 (초기 1회)
  useEffect(() => {
    void initWs();
    const unsub = subscribeStore(() => setTick((v) => v + 1));
    return () => { if (typeof unsub === 'function') unsub(); };
  }, [initWs, subscribeStore]);

  // 추천 데이터 로드 (초기 1회, StrictMode 중복 실행 가드)
  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    (async () => {
      try {
        setIsLoading(true);
        const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;
        if (!accessToken) return;
        const res = await fetch('/api/dashboard/stock/recommendation', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ accessToken, market: 'NASDAQ', strategy: 'MOMENTUM' })
        });
        if (!res.ok) return;
        const data = await res.json();
        // 백엔드가 recommendations 배열로 내려줌
        const arr: RecItemWithColor[] = (data?.recommendations ?? []).map((x: any) => ({
          date: String(x.date ?? ''),
          ticker: String(x.ticker ?? ''),
          reason: String(x.reason ?? ''),
          report: String(x.report ?? ''),
          color: typeof x.color === 'string' ? x.color : undefined,
        }));
        setItems(arr);
        // 추천 종목 실시간 구독 + 초기 REST 가격 큐 등록(전역 큐가 0.5초 간격 직렬 처리)
        for (const it of arr) {
          addSymbol(it.ticker);
        }
        requestPrices(arr.map((x) => x.ticker));
      } catch (e) {
        console.error('recommendation fetch error', e);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const modalItem = openIdx !== null ? items[openIdx] : null;
  const prices = useMemo(() => {
    const out: Record<string, number> = {};
    for (const it of items) {
      const sd = getStock(it.ticker);
      if (sd?.price) out[it.ticker] = sd.price;
    }
    return out;
  }, [items, getStock, tick]);

  return (
    <div className="w-full max-w-7xl bg-gradient-to-br from-black via-gray-900 to-gray-850 rounded-2xl shadow-2xl border border-gray-800 p-4 flex flex-col gap-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
        {(isLoading || items.length === 0)
          ? Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={`skeleton-${i}`} />
            ))
          : items.map((it, i) => {
          const name = TICKER_NAME[it.ticker] ?? it.ticker;
          const price = prices[it.ticker];
          const sd = getStock(it.ticker);
          const delta = sd?.change ?? 0;
          const pct = sd?.changePct ?? 0;
          const isUp = Number.isFinite(delta) ? delta >= 0 : true;
          const dirColor = isUp ? '#ef4444' : '#3b82f6';
          const cardColor = (typeof it.color === 'string' && /^#([0-9A-Fa-f]{6})$/.test(it.color)) ? it.color : '#1f2937';
          const headerBg = hexToRgba(cardColor, 0.1);
          return (
            <button
              key={`${it.ticker}-${i}`}
              onClick={() => setOpenIdx(i)}
              className="group text-left rounded-xl border-0 backdrop-blur-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 shadow-md p-4 flex flex-col items-start min-h-[320px] min-w-[280px] w-full"
              style={{ background: '#0b0b0e', borderColor: cardColor, borderWidth: 1 }}
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
        })}
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
