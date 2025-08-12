"use client"

import React, { useState } from "react";
import { Header } from "@/components/layout/header";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { useRouter } from "next/navigation";
import { useTutorial } from "@/hooks/use-tutorial";
import { TutorialOverlay } from "@/components/tutorial/tutorial-overlay";
import { StrategyGrid } from "@/components/autotrade/strategy-grid";
import { endRouteProgress } from "@/lib/route-progress";

/**
 * Auto-Trading Page
 * TailwindCSS + shadcn/ui + framer-motion
 */
export default function AutoTradingPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const {
    currentTutorial,
    currentStep,
    currentStepInfo,
    nextStep,
    previousStep,
    skipTutorial,
    isLoading: tutorialLoading
  } = useTutorial();

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

  // StrategyGrid의 첫 데이터 로딩 완료 시점을 받아 상단 진행바 종료
  const handleInitialLoadEnd = React.useCallback(() => {
    endRouteProgress();
  }, []);

  return (
    <>
      <Header onSidebarOpen={() => setSidebarOpen(true)} />
      <AppSidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
        onNavigate={handleNavigate}
      />
      <div className="min-h-screen bg-gradient-to-br from-[#0b1221] to-[#02050a] p-6 md:p-10 text-white">
        <StrategyGrid onInitialLoadEnd={handleInitialLoadEnd} />
      </div>
      
      {/* 튜토리얼 오버레이 */}
      <TutorialOverlay
        isVisible={!!currentTutorial && !!currentStepInfo()}
        stepInfo={currentStepInfo()}
        onNext={nextStep}
        onPrevious={previousStep}
        onSkip={skipTutorial}
        currentStep={currentStep}
        totalSteps={currentTutorial === 'SIGNALS' ? 3 : 0}
      />
    </>
  );
}
