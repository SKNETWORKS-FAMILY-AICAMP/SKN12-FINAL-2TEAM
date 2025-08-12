"use client";

import { useEffect, useState } from "react";
import { useAuth }         from "@/hooks/use-auth";
import { useNasdaqStocks } from "@/hooks/use-nasdaq-stocks";
import { useTutorial }     from "@/hooks/use-tutorial";

import WorldIndicesTicker         from "@/components/dashboard/WorldIndicesTicker";
import RecommendStocksCards       from "@/components/dashboard/RecommendStocksCards";
import { MarketOverviewCard }     from "@/components/dashboard/MarketOverviewCard";
import { PortfolioBreakdownCard } from "@/components/dashboard/PortfolioBreakdownCard";
import { AiSignal, AISignalCard } from "@/components/dashboard/AISignalCard";
import { TutorialOverlay }        from "@/components/tutorial/tutorial-overlay";

/* ────────── 가시 종목 ────────── */
const INDEX = ["QQQ", "TQQQ", "SOXL"];
const PORTF = ["005930", "000660", "051910"];

export default function DashboardPageClient() {
  const { accessTokenReady } = useAuth();
  const { initWs, addSymbol, getStock, subscribeStore } = useNasdaqStocks();

  // ✅ 한번만 초기화 + 구독 (성공/실패 분기 추가)
  useEffect(() => {
    console.log("[PAGE] effect fired, accessTokenReady =", accessTokenReady);

    let mounted = true;
    (async () => {
      console.log("[PAGE] call initWs()");
      const ok = await initWs().catch(e => {
        console.error("[PAGE] initWs threw", e);
        return false;
      });
      console.log("[PAGE] initWs() returned =", ok);
      if (!mounted || !ok) return;
      [...INDEX, ...PORTF].forEach(addSymbol);
    })();

    return () => { mounted = false; };
  }, [accessTokenReady, initWs, addSymbol]);

  // ── 시세 상태 ───────────────────────────
  const [marketData, setMarketData] = useState<any[]>([]);
  const [portfolioItems, setPortfolioItems] = useState<any[]>([]);
  const [aiSignals] = useState<AiSignal[]>([
    { label:"삼성전자",      action:"매수", confidence:"92%", change:"+5.1%", reason:"기술적 돌파 + 실적 개선 기대" },
    { label:"LG에너지솔루션", action:"매도", confidence:"78%", change:"-5.6%", reason:"과매수 구간 + 수급 약화" },
  ]);

  // ✅ 스토어 변경 시 즉시 리렌더
  useEffect(() => {
    const recompute = () => {
      setMarketData(
        INDEX.map((s) => {
          const info = getStock(s);
          return {
            label: s,
            value: info?.price ?? 0,
            change: info
      ? `${info.change > 0 ? "+" : ""}${(info.changePct ?? 0).toFixed(2)}%`
      : "N/A",
          };
        })
      );

      setPortfolioItems(
        PORTF.map((s) => ({
          symbol: s,
          name: s === "005930" ? "삼성전자" : s === "000660" ? "SK하이닉스" : "LG화학",
          value : Math.floor(Math.random() * 100000),
          change: `${(Math.random() * 2 - 1).toFixed(2)}%`,
          shares: Math.floor(Math.random() * 100),
        }))
      );
    };

    recompute();                 // 초기 1회
    return subscribeStore(recompute);
  }, [getStock, subscribeStore]);

  /* ────────── 튜토리얼 훅 ────────── */
  const {
    currentTutorial, currentStep, currentStepInfo,
    nextStep, previousStep, skipTutorial,
  } = useTutorial();

  /* ────────── UI ────────── */
  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
      <WorldIndicesTicker />

      <main className="flex-1 flex flex-col items-center px-6 md:px-12 py-2">
        <h1 className="text-2xl md:text-3xl font-bold mb-2 max-w-7xl w-full">
          Professional{" "}
          <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            AI Trading Dashboard
          </span>
        </h1>

        <RecommendStocksCards />

        <div className="w-full flex justify-center">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-2 max-w-7xl">
            <MarketOverviewCard     markets={marketData}   />
            <PortfolioBreakdownCard items={portfolioItems} />
            <AISignalCard           signals={aiSignals}    />
          </div>
        </div>
      </main>

      <TutorialOverlay
        isVisible={!!currentTutorial && !!currentStepInfo()}
        stepInfo={currentStepInfo()}
        onNext={nextStep}
        onPrevious={previousStep}
        onSkip={skipTutorial}
        currentStep={currentStep}
        totalSteps={currentTutorial === "OVERVIEW" ? 6 : 0}
      />
    </div>
  );
}
