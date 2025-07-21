import React from "react";

interface PortfolioValueCardProps {
  value: string | number;
  change: string;
}

export function PortfolioValueCard({ value, change }: PortfolioValueCardProps) {
  const isPositive = change.startsWith("+");
  return (
    <div className="metric-card p-4">
      <div className="metric-label text-sm">Portfolio Value</div>
      <div className="metric-value text-lg">{value}</div>
      <div className="metric-change text-sm">
        <span>↗</span>
        <span className={isPositive ? "text-emerald-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 