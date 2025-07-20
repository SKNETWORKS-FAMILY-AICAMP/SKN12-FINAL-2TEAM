import React from "react";

interface WinRateCardProps {
  value: string;
  change: string;
}

export function WinRateCard({ value, change }: WinRateCardProps) {
  const isPositive = change.startsWith("+");
  return (
    <div className="metric-card p-4">
      <div className="metric-label text-sm">Win Rate</div>
      <div className="metric-value text-lg">{value}</div>
      <div className="metric-change text-sm">
        <span>↗</span>
        <span className={isPositive ? "text-emerald-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 