import React, { useRef, useEffect, useState } from "react";

const mockIndices = [
  { symbol: "NASDAQ", price: 17800.12, change: +0.45 },
  { symbol: "S&P500", price: 5200.34, change: -0.12 },
  { symbol: "DAX", price: 16200.56, change: +0.22 },
  { symbol: "NIKKEI", price: 39000.78, change: +1.12 },
  { symbol: "GOLD", price: 2350.12, change: -0.08 },
  { symbol: "KOSPI", price: 2700.45, change: +0.31 },
  { symbol: "FTSE100", price: 8000.12, change: -0.15 },
  { symbol: "HANGSENG", price: 18500.67, change: +0.67 },
];

export default function WorldIndicesTicker() {
  const [widths, setWidths] = useState<number[]>([]);
  const refs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    setWidths(refs.current.map(ref => ref?.offsetWidth || 0));
  }, []);

  return (
    <div className="relative w-full overflow-hidden bg-black border-b border-gray-800" style={{ height: 40 }}>
      <div className="animate-marquee flex flex-nowrap items-center h-full gap-4">
        {mockIndices.concat(mockIndices).map((idx, i) => {
          const isUp = idx.change > 0;
          const isDown = idx.change < 0;
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          const arrow = isUp ? "▲" : isDown ? "▼" : "-";
          return (
            <div
              key={idx.symbol + i}
              ref={el => refs.current[i] = el}
              className="flex items-center gap-1 flex-shrink-0 whitespace-nowrap"
              style={{ minWidth: 80 }}
            >
              <span className="font-light text-sm tracking-wide" style={{ letterSpacing: 1 }}>{idx.symbol}</span>
              <span className={`font-light text-base ${color}`}>{idx.price.toLocaleString()}</span>
              <span className={`ml-1 ${color} text-lg font-light`}>{arrow}</span>
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