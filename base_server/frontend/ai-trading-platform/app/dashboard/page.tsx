"use client"

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart2, PieChart, Activity } from "lucide-react"
import { PortfolioValueCard } from "@/components/dashboard/PortfolioValueCard";
import { ActivePositionsCard } from "@/components/dashboard/ActivePositionsCard";
import { MonthlyReturnCard } from "@/components/dashboard/MonthlyReturnCard";
import { WinRateCard } from "@/components/dashboard/WinRateCard";
import { MarketOverviewCard } from "@/components/dashboard/MarketOverviewCard";
import { PortfolioBreakdownCard } from "@/components/dashboard/PortfolioBreakdownCard";
import { AISignalCard } from "@/components/dashboard/AISignalCard";
import { DashboardActions } from "@/components/dashboard/DashboardActions";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Header } from "@/components/layout/header";

export default function DashboardPage() {
  // sidebarOpen and setSidebarOpen should be managed in parent layout, not here
  const router = useRouter();

  const handleNavigate = (key: string) => {
    switch (key) {
      case "dashboard":
        router.push("/dashboard"); break;
      case "portfolio":
        router.push("/portfolio"); break;
      case "signals":
        router.push("/signals"); break;
      case "settings":
        router.push("/settings"); break;
      default:
        break;
    }
  };

  const marketData = [
    { label: "KOSPI", value: 2485, change: "+0.5%" },
    { label: "S&P 500", value: 4567, change: "+0.52%" },
    { label: "KOSDAQ", value: 845.2, change: "-0.67%" },
  ];
  const portfolioItems = [
    { label: "삼성전자", change: "+5.38%" },
    { label: "SK하이닉스", change: "-4.17%" },
    { label: "LG에너지솔루션", change: "+2.12%" },
  ];
  const aiSignals = [
    {
      label: "삼성전자",
      action: "매수",
      confidence: "92%",
      change: "+5.1%",
      reason: "기술적 돌파 + 실적 개선 기대",
    },
    {
      label: "LG에너지솔루션",
      action: "매도",
      confidence: "78%",
      change: "-5.6%",
      reason: "과매수 구간 + 수급 약화",
    },
  ];

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#0a0a0a] via-[#18181c] to-[#23243a] text-white flex">
      {/* AppSidebar should be rendered in the parent layout, not here */}
      <main className="flex-1 flex flex-col items-center px-4 md:px-12 py-16 bg-transparent min-h-screen">
        <h1 className="text-4xl md:text-5xl font-bold mb-10 tracking-tight text-white text-balance">
          Professional <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">AI Trading Dashboard</span>
        </h1>
        <div className="dashboard w-full max-w-5xl mb-12">
          <div className="dashboard-grid">
            <PortfolioValueCard value="$847,296" change="+18.4%" />
            <ActivePositionsCard value={12} change="+3" />
            <MonthlyReturnCard value="24.7%" change="+5.2%" />
            <WinRateCard value="87%" change="+12%" />
            {/* Chart Visualization (optional, keep if needed) */}
            <div className="chart-visualization">
              <div className="chart-line"></div>
            </div>
          </div>
        </div>
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <MarketOverviewCard markets={marketData} />
          <PortfolioBreakdownCard items={portfolioItems} />
          <AISignalCard signals={aiSignals} />
        </div>
        <DashboardActions
          onStartTrading={() => alert("Start Trading!")}
          onViewDemo={() => alert("View Demo!")}
        />
      </main>
    </div>
  );
}
