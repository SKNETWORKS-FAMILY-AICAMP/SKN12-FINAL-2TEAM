"use client"

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { BarChart2, PieChart, Activity } from "lucide-react"
import { PortfolioValueCard } from "@/components/dashboard/PortfolioValueCard";
import { ActivePositionsCard } from "@/components/dashboard/ActivePositionsCard";
import { MonthlyReturnCard } from "@/components/dashboard/MonthlyReturnCard";
import { WinRateCard } from "@/components/dashboard/WinRateCard";
import { MarketOverviewCard } from "@/components/dashboard/MarketOverviewCard";
import { PortfolioBreakdownCard } from "@/components/dashboard/PortfolioBreakdownCard";
import { AISignalCard } from "@/components/dashboard/AISignalCard";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Header } from "@/components/layout/header";

export default function DashboardPage() {
  // sidebarOpen and setSidebarOpen should be managed in parent layout, not here
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;
    if (!token) {
      window.location.href = "/auth/login";
    } else {
      setChecked(true);
    }
  }, [router]);

  if (!checked) return null;

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
    <div className="h-screen w-full bg-gradient-to-br from-[#0a0a0a] via-[#18181c] to-[#23243a] text-white flex overflow-hidden">
      <main className="flex-1 flex flex-col items-center px-6 md:px-12 py-8 bg-transparent overflow-hidden">
        <h1 className="text-4xl md:text-6xl font-bold mb-8 tracking-tight text-white text-balance">
          Professional <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">AI Trading Dashboard</span>
        </h1>
        <div className="dashboard w-full max-w-6xl mb-8">
          <div className="dashboard-grid">
            <PortfolioValueCard value="$847,296" change="+18.4%" />
            <ActivePositionsCard value={12} change="+3" />
            <MonthlyReturnCard value="24.7%" change="+5.2%" />
            <WinRateCard value="87%" change="+12%" />
          </div>
        </div>
        <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-3 gap-6">
          <MarketOverviewCard markets={marketData} />
          <PortfolioBreakdownCard items={portfolioItems} />
          <AISignalCard signals={aiSignals} />
        </div>
      </main>
    </div>
  );
}
