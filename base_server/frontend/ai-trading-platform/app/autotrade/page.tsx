"use client"

import React, { useState } from "react";
import { Header } from "@/components/layout/header";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { useRouter } from "next/navigation";
import { StrategyGrid } from "@/components/autotrade/strategy-grid";

/**
 * Auto-Trading Page
 * TailwindCSS + shadcn/ui + framer-motion
 */
export default function AutoTradingPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // 페이지 이동 핸들러
  const handleNavigate = (key: string) => {
    switch (key) {
      case "dashboard":
        router.push("/dashboard"); break;
      case "portfolio":
        router.push("/portfolio"); break;
      case "signals":
        router.push("/autotrade"); break;
      case "chat":
        router.push("/chat"); break;
      case "settings":
        router.push("/settings"); break;
      default:
        break;
    }
    setSidebarOpen(false);
  };

  return (
    <>
      <Header onSidebarOpen={() => setSidebarOpen(true)} />
      <AppSidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
        onNavigate={handleNavigate}
      />
      <div className="min-h-screen bg-gradient-to-br from-[#0b1221] to-[#02050a] p-6 md:p-10 text-white">
        <StrategyGrid />
      </div>
    </>
  );
}
