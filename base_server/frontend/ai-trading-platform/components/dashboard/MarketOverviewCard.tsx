import React from "react";

export function MarketOverviewCard({ markets }: { markets: { label: string; value: number; change: string }[] }) {
  return (
    <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-6 min-w-[260px] flex flex-col items-start w-full max-w-sm border border-gray-800">
      <div className="text-lg font-bold mb-4 text-white">Market Overview</div>
      <div className="flex flex-col gap-4 w-full">
        {markets.map((m) => {
          const isUp = m.change.startsWith("+");
          const isDown = m.change.startsWith("-");
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          return (
            <div key={m.label} className="flex flex-col gap-1 w-full">
              <div className="flex items-center justify-between w-full">
                <span className="text-base font-semibold text-white">{m.label}</span>
                <span className="text-xl font-bold text-white">{m.value.toLocaleString()}</span>
              </div>
              <div className={`text-base font-bold ${color} leading-relaxed`}>{m.change}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
} 