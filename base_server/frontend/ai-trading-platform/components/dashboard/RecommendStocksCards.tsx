import React, { useState, useEffect } from "react";
// import { useKoreaInvestApi } from '@/hooks/use-korea-invest-api'; // 🔥 제거함
import { useWebSocketStockData } from '@/hooks/use-websocket-stock-data';

const mockStocks = [
  {
    name: "삼성전자",
    symbol: "005930.KS",
    price: 78500,
    change: +1.23,
    desc: "AI 반도체 수혜 기대감 지속.\n글로벌 파운드리 시장 점유율 확대 기대.\n외국인 순매수세 유입.",
    logo: "S",
    chart: [1, 2, 2.5, 2, 3, 3.5, 4],
    gradient: "from-blue-900 to-purple-900",
  },
  {
    name: "테슬라",
    symbol: "TSLA",
    price: 245.12,
    change: -2.15,
    desc: "실적 부진 우려로 하락세.\n전기차 수요 둔화 및 원가 부담 증가.\n단기 변동성 확대 예상.",
    logo: "T",
    chart: [4, 3.5, 3, 2.5, 2, 1.5, 1],
    gradient: "from-green-900 to-blue-900",
  },
  {
    name: "엔비디아",
    symbol: "NVDA",
    price: 125.67,
    change: +3.45,
    desc: "GPU 수요 급증, 목표가 상향.\nAI 서버 시장 성장 수혜.\n기관 매수세 지속.",
    logo: "N",
    chart: [2, 2.2, 2.5, 2.8, 3.2, 3.8, 4.5],
    gradient: "from-yellow-900 to-red-900",
  },
];

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

export default function RecommendStocksCards() {
  const [hasValidData, setHasValidData] = useState(false);

  // const { hasApiKey, isLoading: apiLoading, marketDataManager } = useKoreaInvestApi(); // 🔥 제거함
  const { isConnected: wsConnected, getWsStockData } = useWebSocketStockData();

  return (
    <div className="w-full max-w-7xl bg-gradient-to-br from-black via-gray-900 to-gray-850 rounded-2xl shadow-2xl border border-gray-800 p-4 flex flex-col gap-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
        {mockStocks.map((stock, i) => {
          const isUp = stock.change > 0;
          const isDown = stock.change < 0;
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          const arrow = isUp ? "▲" : isDown ? "▼" : "-";
          const chartColor = isUp ? "#4ade80" : isDown ? "#f87171" : "#a3a3a3";
          return (
            <div
              key={stock.symbol}
              className={`group rounded-xl border-0 bg-white/80 dark:bg-[#18181c]/80 backdrop-blur-xl hover:shadow-2xl transition-all duration-500 hover:scale-105 shadow-md p-4 flex flex-col items-start min-h-[320px] min-w-[280px] w-full bg-gradient-to-br ${stock.gradient}`}
            >
              <div className="flex items-center w-full mb-3">
                <div className="w-12 h-12 rounded-full bg-white text-black font-bold text-xl flex items-center justify-center mr-5 shadow">
                  {stock.logo}
                </div>
                <div className="flex-1">
                  <div className="text-xl font-bold leading-tight">{stock.name}</div>
                  <div className="text-sm text-gray-400 font-semibold">{stock.symbol}</div>
                </div>
              </div>
              <div className="flex items-center justify-between w-full mb-3">
                <div className="flex items-center">
                  <span className="text-2xl font-extrabold mr-4">{stock.price.toLocaleString()}</span>
                  <span className={`font-bold ${color} flex items-center text-xl mr-3`}>{arrow}</span>
                </div>
                <div className="-mt-16">
                  <Sparkline data={stock.chart} color={chartColor} />
                </div>
              </div>
              <div className="mt-auto w-full pt-2">
                <div className="text-sm text-gray-400 mb-1 font-semibold">추천 사유</div>
                <div className="text-sm text-gray-300 whitespace-pre-line leading-relaxed">
                  {stock.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
