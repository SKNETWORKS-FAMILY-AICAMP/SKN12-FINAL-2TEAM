import React from "react";

interface PortfolioItem {
  label: string;
  change: string;
}

interface PortfolioBreakdownCardProps {
  items: PortfolioItem[];
}

export function PortfolioBreakdownCard({ items }: PortfolioBreakdownCardProps) {
  return (
    <div className="metric-card flex flex-col items-start">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold text-white/90">Portfolio Breakdown</span>
      </div>
      {items.map((item) => (
        <div key={item.label} className="text-base text-gray-400">
          {item.label} <span className={item.change.startsWith("+") ? "text-emerald-400 font-bold ml-2" : "text-red-400 font-bold ml-2"}>{item.change}</span>
        </div>
      ))}
    </div>
  );
} 