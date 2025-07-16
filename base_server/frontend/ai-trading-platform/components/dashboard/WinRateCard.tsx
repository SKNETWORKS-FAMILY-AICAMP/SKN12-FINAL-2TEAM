import React from "react";

interface WinRateCardProps {
  value: string | number;
  change: string;
}

export function WinRateCard({ value, change }: WinRateCardProps) {
  const isPositive = change.startsWith("+");
  return (
    <div className="metric-card">
      <div className="metric-label">Win Rate</div>
      <div className="metric-value">{value}</div>
      <div className="metric-change">
        <span>↗</span>
        <span className={isPositive ? "text-emerald-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 