import React, { useRef, useEffect, useState } from "react";

// 기본 N/A 데이터 (웹소켓 데이터가 없을 때 표시)
const defaultIndices = [
  { symbol: "NASDAQ", price: 0, change: 0, isNA: true },
  { symbol: "S&P500", price: 0, change: 0, isNA: true },
  { symbol: "DAX", price: 0, change: 0, isNA: true },
  { symbol: "NIKKEI", price: 0, change: 0, isNA: true },
  { symbol: "GOLD", price: 0, change: 0, isNA: true },
  { symbol: "KOSPI", price: 0, change: 0, isNA: true },
  { symbol: "FTSE100", price: 0, change: 0, isNA: true },
  { symbol: "HANGSENG", price: 0, change: 0, isNA: true },
];

interface WorldIndicesTickerProps {
  marketData?: {
    kospi?: { current_price: number; change_rate: number };
    kosdaq?: { current_price: number; change_rate: number };
    sp500?: { current_price: number; change_rate: number };
  };
}

export default function WorldIndicesTicker({ marketData }: WorldIndicesTickerProps) {
  const [indices, setIndices] = useState(defaultIndices);
  const [widths, setWidths] = useState<number[]>([]);
  const refs = useRef<Map<number, HTMLDivElement | null>>(new Map());

  // 실시간 데이터로 업데이트
  useEffect(() => {
    if (marketData && Object.keys(marketData).length > 0) {
      const updatedIndices = [...defaultIndices];
      
      // KOSPI 업데이트
      if (marketData.kospi && marketData.kospi.current_price > 0) {
        const kospiIndex = updatedIndices.findIndex(idx => idx.symbol === "KOSPI");
        if (kospiIndex !== -1) {
          updatedIndices[kospiIndex] = {
            symbol: "KOSPI",
            price: marketData.kospi.current_price,
            change: marketData.kospi.change_rate,
            isNA: false
          };
        }
      } else {
        // KOSPI 데이터 없음 - N/A 표시
        const kospiIndex = updatedIndices.findIndex(idx => idx.symbol === "KOSPI");
        if (kospiIndex !== -1) {
          updatedIndices[kospiIndex] = {
            symbol: "KOSPI",
            price: 0,
            change: 0,
            isNA: true
          };
        }
      }
      
      // KOSDAQ 업데이트
      if (marketData.kosdaq && marketData.kosdaq.current_price > 0) {
        const kosdaqIndex = updatedIndices.findIndex(idx => idx.symbol === "NASDAQ");
        if (kosdaqIndex !== -1) {
          updatedIndices[kosdaqIndex] = {
            symbol: "KOSDAQ",
            price: marketData.kosdaq.current_price,
            change: marketData.kosdaq.change_rate,
            isNA: false
          };
        }
      } else {
        // KOSDAQ 데이터 없음 - N/A 표시
        const kosdaqIndex = updatedIndices.findIndex(idx => idx.symbol === "NASDAQ");
        if (kosdaqIndex !== -1) {
          updatedIndices[kosdaqIndex] = {
            symbol: "KOSDAQ",
            price: 0,
            change: 0,
            isNA: true
          };
        }
      }
      
      // S&P 500 업데이트
      if (marketData.sp500 && marketData.sp500.current_price > 0) {
        const sp500Index = updatedIndices.findIndex(idx => idx.symbol === "S&P500");
        if (sp500Index !== -1) {
          updatedIndices[sp500Index] = {
            symbol: "S&P500",
            price: marketData.sp500.current_price,
            change: marketData.sp500.change_rate,
            isNA: false
          };
        }
      } else {
        // S&P 500 데이터 없음 - N/A 표시
        const sp500Index = updatedIndices.findIndex(idx => idx.symbol === "S&P500");
        if (sp500Index !== -1) {
          updatedIndices[sp500Index] = {
            symbol: "S&P500",
            price: 0,
            change: 0,
            isNA: true
          };
        }
      }
      
      setIndices(updatedIndices);
    } else {
      // 웹소켓 데이터가 없으면 모든 지수를 N/A로 표시
      console.log("웹소켓 데이터 없음, 모든 지수를 N/A로 표시");
      setIndices(defaultIndices);
    }
  }, [marketData]);

  useEffect(() => {
    const widthArray = Array.from(refs.current.values()).map(ref => ref?.offsetWidth || 0);
    setWidths(widthArray);
  }, [indices]);

  return (
    <div className="relative w-full overflow-hidden bg-black border-b border-gray-800" style={{ height: 40 }}>
      <div className="animate-marquee flex flex-nowrap items-center h-full gap-4">
        {indices.concat(indices).map((idx, i) => {
          const isUp = idx.change > 0;
          const isDown = idx.change < 0;
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          const arrow = isUp ? "▲" : isDown ? "▼" : "-";
          return (
            <div
              key={idx.symbol + i}
              ref={(el) => {
                refs.current.set(i, el);
              }}
              className="flex items-center gap-1 flex-shrink-0 whitespace-nowrap"
              style={{ minWidth: 80 }}
            >
              <span className="font-light text-sm tracking-wide" style={{ letterSpacing: 1 }}>{idx.symbol}</span>
              {idx.isNA ? (
                <span className="font-light text-base text-gray-500">N/A</span>
              ) : (
                <>
                  <span className={`font-light text-base ${color}`}>{idx.price.toLocaleString()}</span>
                  <span className={`ml-1 ${color} text-lg font-light`}>{arrow}</span>
                </>
              )}
            </div>
          );
        })}
      </div>
      <style jsx>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 24s linear infinite;
        }
      `}</style>
    </div>
  );
} 