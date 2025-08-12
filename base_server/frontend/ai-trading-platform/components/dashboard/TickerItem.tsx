"use client";
import React, { useEffect, useState } from "react";
import { StockInfoStore } from "@/hooks/use-nasdaq-stocks";
import { useNasdaqStocks } from "@/hooks/use-nasdaq-stocks";

type Props = {
  symbol: string;
  /** 마운트 시 해당 심볼을 한 번 구독할지 (기본값: true) */
  autoSubscribe?: boolean;
  /** 폴링 주기(ms). 기본 1000 */
  intervalMs?: number;
  /** 구독 지연(ms). 기본 0 - 레이트 리밋 회피용 순차 딜레이 */
  subscribeDelayMs?: number;
};

export default function TickerItem({ symbol, autoSubscribe = true, intervalMs = 1000, subscribeDelayMs = 0 }: Props) {
  const { addSymbol } = useNasdaqStocks();
  const [data, setData] = useState(() => StockInfoStore.get(symbol)); // 초기 스냅샷

  // 1) (선택) 심볼 한 번 구독
  useEffect(() => {
    if (!autoSubscribe) return;
    const id = window.setTimeout(() => {
      addSymbol(symbol);
    }, Math.max(0, subscribeDelayMs));
    return () => window.clearTimeout(id);
  }, [symbol, autoSubscribe, addSymbol, subscribeDelayMs]);

  // 2) 1초마다 전역 스토어에서 폴링
  useEffect(() => {
    if (typeof window === "undefined") return;
    // 즉시 1회 갱신
    setData(StockInfoStore.get(symbol));

    const id = setInterval(() => {
      setData(StockInfoStore.get(symbol));
    }, Math.max(250, intervalMs)); // 최소 250ms 안전장치

    return () => clearInterval(id);
  }, [symbol, intervalMs]);

  // 렌더 로깅(원하면 유지)
  console.log(
    `%c[RENDER-POLL] ${symbol} →`,
    "color:gray",
    data ? `${data.price}` : "loading"
  );

  // 데이터 디버깅 로그 추가
  if (data) {
    console.log(`%c[TickerItem] ${symbol} 데이터:`, "color:cyan", {
      price: data.price,
      change: data.change,
      changePct: data.changePct,
      volume: data.volume,
      timestamp: data.timestamp
    });
  }

  // 안전 포맷팅
  const priceNum = data?.price ?? 0;
  const changeNum = data?.change ?? 0;
  const pctNum = data?.changePct ?? 0;

  // 변동률을 기준으로 색상과 방향 결정 (변동률이 더 정확함)
  const changeClass =
    !data ? "text-gray-500"
    : pctNum > 0 ? "text-red-400"
    : pctNum < 0 ? "text-blue-400"
    : "text-gray-400";

  const sign = !data ? "" : pctNum > 0 ? "▲" : pctNum < 0 ? "▼" : "-";

  return (
    <div className="ticker-item">
      <span className="font-bold text-sm text-gray-300">{symbol}</span>
      {data ? (
        <>
          <span className={`ml-3 font-semibold ${changeClass}`}>
            {Number.isFinite(priceNum) ? priceNum.toLocaleString() : "0"}
          </span>
          <span className={`ml-2 text-xs ${changeClass}`}>
            {sign} {Number.isFinite(changeNum) ? (pctNum >= 0 ? '+' : '-') + Math.abs(changeNum).toLocaleString() : "0"} (
            {Number.isFinite(pctNum) ? (pctNum >= 0 ? '+' : '') + pctNum.toFixed(2) : "0.00"}%)
          </span>
        </>
      ) : (
        <span className="ml-3 text-gray-500">loading…</span>
      )}
    </div>
  );
}
