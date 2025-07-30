import React from "react";

export function AISignalCard({ signals }: { signals: { label: string; action: string; confidence: string; change: string; reason: string }[] }) {
  return (
    <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
      <div className="text-base font-bold mb-2 text-white">AI Trading Signal</div>
      <div className="flex flex-col gap-2 w-full">
        {signals.map((s, i) => {
          const isUp = s.change.startsWith("+");
          const isDown = s.change.startsWith("-");
          const color = isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-300";
          return (
            <div key={s.label + i} className="flex flex-col gap-1 w-full">
              <div className="flex items-center justify-between w-full">
                <span className="text-sm font-semibold text-white">{s.label}</span>
                <span className={`text-sm font-bold ${color}`}>{s.change}</span>
              </div>
              <div className="text-xs text-gray-400 leading-tight">{s.action} | {s.confidence} | {s.reason.substring(0, 20)}...</div>
            </div>
          );
        })}
      </div>
    </div>
  );
} 