import React from "react";

interface DashboardActionsProps {
  onStartTrading?: () => void;
  onViewDemo?: () => void;
}

export function DashboardActions({ onStartTrading, onViewDemo }: DashboardActionsProps) {
  return (
    <div className="flex gap-6 mt-4">
      <button
        className="btn btn-primary btn-large bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold shadow-lg"
        onClick={onStartTrading}
      >
        Start Trading
      </button>
      <button
        className="btn btn-secondary btn-large border border-white/20 text-white/80 hover:bg-white/10"
        onClick={onViewDemo}
      >
        View Demo
      </button>
    </div>
  );
} 