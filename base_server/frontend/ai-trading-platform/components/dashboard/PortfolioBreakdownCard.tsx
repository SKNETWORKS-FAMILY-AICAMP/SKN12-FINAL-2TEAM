import React from "react";

export function PortfolioBreakdownCard({ items }: { items: { label: string; change: string }[] }) {
  return (
    <div className="bg-[#23243a] rounded-xl shadow-lg p-6 min-w-[260px] flex flex-col items-start w-full max-w-sm border border-[#353657]">
      <div className="text-lg font-bold mb-4 text-white">Portfolio Breakdown</div>
      <div className="flex flex-col gap-4 w-full">
        {items.map((item) => {
          const isUp = item.change.startsWith("+");
          const isDown = item.change.startsWith("-");
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          return (
            <div key={item.label} className="flex items-center justify-between w-full">
              <span className="text-base font-semibold text-white">{item.label}</span>
              <span className={`text-base font-bold ${color} leading-relaxed`}>{item.change}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
} 