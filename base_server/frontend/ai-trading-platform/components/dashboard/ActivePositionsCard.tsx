import React from "react";

export function ActivePositionsCard({ value, change }: { value: number; change: string }) {
  const isPositive = change.startsWith("+");
  return (
    <div className="bg-[#23243a] rounded-xl shadow-lg p-6 min-w-[180px] flex flex-col items-start w-full max-w-xs border border-[#353657]">
      <div className="text-base font-bold mb-2 text-white">Active Positions</div>
      <div className="text-2xl font-extrabold text-white mb-1">{value}</div>
      <div className="text-base font-bold leading-relaxed">
        <span className={isPositive ? "text-green-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 