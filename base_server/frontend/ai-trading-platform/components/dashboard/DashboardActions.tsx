import React from "react";

interface DashboardActionsProps {
  onStartTrading?: () => void;
  onViewDemo?: () => void;
}

export function DashboardActions({ onStartTrading, onViewDemo }: DashboardActionsProps) {
  return (
    <div className="flex gap-3 mt-2">
      <button
        className="btn btn-primary bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold shadow-lg text-xs px-3 py-1.5 h-8"
        onClick={onStartTrading}
      >
        Start Trading
      </button>
      <button
        className="btn btn-secondary border border-white/20 text-white/80 hover:bg-white/10 text-xs px-3 py-1.5 h-8"
        onClick={onViewDemo}
      >
        View Demo
      </button>
    </div>
  );
} 