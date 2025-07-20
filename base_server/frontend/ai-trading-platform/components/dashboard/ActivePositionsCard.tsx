import React from "react";

interface ActivePositionsCardProps {
  value: number;
  change: string;
}

export function ActivePositionsCard({ value, change }: ActivePositionsCardProps) {
  const isPositive = change.startsWith("+");
  return (
    <div className="metric-card p-4">
      <div className="metric-label text-sm">Active Positions</div>
      <div className="metric-value text-lg">{value}</div>
      <div className="metric-change text-sm">
        <span>↗</span>
        <span className={isPositive ? "text-emerald-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 