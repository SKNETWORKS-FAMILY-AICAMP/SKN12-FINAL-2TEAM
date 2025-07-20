import React from "react";

interface MonthlyReturnCardProps {
  value: string;
  change: string;
}

export function MonthlyReturnCard({ value, change }: MonthlyReturnCardProps) {
  const isPositive = change.startsWith("+");
  return (
    <div className="metric-card p-4">
      <div className="metric-label text-sm">Monthly Return</div>
      <div className="metric-value text-lg">{value}</div>
      <div className="metric-change text-sm">
        <span>↗</span>
        <span className={isPositive ? "text-emerald-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 