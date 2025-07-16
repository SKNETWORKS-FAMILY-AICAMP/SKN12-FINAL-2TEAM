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
    <div className="metric-card flex flex-col items-start">
      <div className="font-semibold text-white/90 mb-2">AI Trading Signal</div>
      {signals.map((signal) => (
        <div key={signal.label} className="mb-4 w-full">
          <div className="font-bold text-white">{signal.label}</div>
          <div className="text-xs text-gray-400">{signal.action} | 신뢰도 {signal.confidence}</div>
          <div className={signal.change.startsWith("+") ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>{signal.change}</div>
          <div className="text-xs text-gray-500 mt-1">{signal.reason}</div>
        </div>
      ))}
    </div>
  );
} 