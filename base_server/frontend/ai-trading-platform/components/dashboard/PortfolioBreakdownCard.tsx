"use client";

import React from "react";

interface PortfolioItem {
  label: string;       // 예: "삼성전자"
  change: string;      // 예: "+1.24%" 또는 "-0.55%"
}

export function PortfolioBreakdownCard({ items }: { items: PortfolioItem[] }) {
  return (
    <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
      <div className="text-base font-bold mb-2 text-white">Portfolio Breakdown</div>
      <div className="flex flex-col gap-2 w-full">
        {items.map((item, index) => {
          const isUp = item.change.startsWith("+");
          const isDown = item.change.startsWith("-");
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";

          return (
            <div key={`${item.label}-${index}`} className="flex items-center justify-between w-full">
              <span className="text-sm font-semibold text-white">{item.label}</span>
              <span className={`text-sm font-bold ${color} leading-relaxed`}>{item.change}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
