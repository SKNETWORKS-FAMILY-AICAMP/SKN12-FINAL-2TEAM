import React from "react";

export function AISignalCard({ signals }: { signals: { label: string; action: string; confidence: string; change: string; reason: string }[] }) {
  return (
    <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-6 min-w-[260px] flex flex-col items-start w-full max-w-sm border border-gray-800">
      <div className="text-lg font-bold mb-4 text-white">AI Trading Signal</div>
      <div className="flex flex-col gap-4 w-full">
        {signals.map((s, i) => {
          const isUp = s.change.startsWith("+");
          const isDown = s.change.startsWith("-");
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          return (
            <div key={s.label + i} className="flex flex-col gap-1 w-full">
              <div className="flex items-center justify-between w-full">
                <span className="text-base font-semibold text-white">{s.label}</span>
                <span className={`text-base font-bold ${color}`}>{s.change}</span>
              </div>
              <div className="text-xs text-gray-400 leading-relaxed">{s.action} | 신뢰도 {s.confidence} | {s.reason}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
} 