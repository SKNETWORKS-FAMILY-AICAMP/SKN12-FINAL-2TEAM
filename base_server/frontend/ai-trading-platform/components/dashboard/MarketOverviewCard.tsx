import React from "react";

interface MarketItem {
  label: string;
  value: string | number;
  change: string;
}

interface MarketOverviewCardProps {
  markets: MarketItem[];
}

export function MarketOverviewCard({ markets }: MarketOverviewCardProps) {
  return (
    <div className="metric-card flex flex-col items-start p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold text-white/90 text-xs">Market Overview</span>
      </div>
      {markets.map((item) => (
        <div key={item.label} className="text-xs text-gray-400">
          {item.label} <span className={item.change.startsWith("+") ? "text-emerald-400 font-bold ml-1" : "text-red-400 font-bold ml-1"}>{item.value} ({item.change})</span>
        </div>
      ))}
    </div>
  );
} 