import React from "react";

interface PortfolioValueCardProps {
  value: string | number;
  change: string;
}

export function PortfolioValueCard({ value, change }: PortfolioValueCardProps) {
  const isPositive = change.startsWith("+");
  return (
    <div className="metric-card">
      <div className="metric-label">Portfolio Value</div>
      <div className="metric-value">{value}</div>
      <div className="metric-change">
        <span>↗</span>
        <span className={isPositive ? "text-emerald-400" : "text-red-400"}>{change}</span>
      </div>
    </div>
  );
} 