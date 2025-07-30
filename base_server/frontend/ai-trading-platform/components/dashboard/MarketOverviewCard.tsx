import React from "react";

export function MarketOverviewCard({ markets }: { markets: { label: string; value: number; change: string }[] }) {
  return (
    <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
      <div className="text-base font-bold mb-2 text-white">Market Overview</div>
      <div className="flex flex-col gap-2 w-full">
        {markets.map((m) => {
          const isUp = m.change.startsWith("+");
          const isDown = m.change.startsWith("-");
          const isNA = m.value === 0 || m.change === "N/A";
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          return (
            <div key={m.label} className="flex flex-col gap-1 w-full">
              <div className="flex items-center justify-between w-full">
                <span className="text-sm font-semibold text-white">{m.label}</span>
                <span className="text-base font-bold text-white">
                  {isNA ? "N/A" : m.value.toLocaleString()}
                </span>
              </div>
              <div className={`text-xs font-bold ${isNA ? "text-gray-500" : color} leading-relaxed`}>
                {isNA ? "N/A" : m.change}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
} 