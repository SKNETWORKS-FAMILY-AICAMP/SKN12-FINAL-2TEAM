import React from "react";

interface ActivePositionsCardProps {
  value: number;
  change: string;
}

export function ActivePositionsCard({ value, change }: ActivePositionsCardProps) {
  const isPositive = change.startsWith("+");
  return (
    <div className="metric-card">
      <div className="metric-label">Active Positions</div>
      <div className="metric-value">{value}</div>
      <div className="metric-change">
        <span>↗</span>
        <span className={isPositive ? "text-emerald-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 