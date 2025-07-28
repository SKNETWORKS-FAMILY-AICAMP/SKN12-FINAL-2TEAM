import React from "react";

export function WinRateCard({ value, change }: { value: string; change: string }) {
  const isPositive = change.startsWith("+");
  return (
    <div className="bg-gradient-to-br from-gray-900 via-gray-900 to-gray-700 rounded-xl shadow-lg p-6 min-w-[180px] flex flex-col items-start w-full max-w-xs border border-gray-800">
      <div className="text-base font-bold mb-2 text-white">Win Rate</div>
      <div className="text-2xl font-extrabold text-white mb-1">{value}</div>
      <div className="text-base font-bold leading-relaxed">
        <span className={isPositive ? "text-green-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 