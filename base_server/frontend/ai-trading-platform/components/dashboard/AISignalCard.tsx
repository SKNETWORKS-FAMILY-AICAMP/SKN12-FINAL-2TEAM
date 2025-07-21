import React from "react";

interface AISignal {
  label: string;
  action: string;
  confidence: string;
  change: string;
  reason: string;
}

interface AISignalCardProps {
  signals: AISignal[];
}

export function AISignalCard({ signals }: AISignalCardProps) {
  return (
    <div className="metric-card flex flex-col items-start p-3">
      <div className="font-semibold text-white/90 mb-2 text-xs">AI Trading Signal</div>
      {signals.map((signal) => (
        <div key={signal.label} className="mb-2 w-full">
          <div className="font-bold text-white text-xs">{signal.label}</div>
          <div className="text-xs text-gray-400">{signal.action} | 신뢰도 {signal.confidence}</div>
          <div className={signal.change.startsWith("+") ? "text-emerald-400 font-bold text-xs" : "text-red-400 font-bold text-xs"}>{signal.change}</div>
          <div className="text-xs text-gray-500 mt-0.5">{signal.reason}</div>
        </div>
      ))}
    </div>
  );
} 