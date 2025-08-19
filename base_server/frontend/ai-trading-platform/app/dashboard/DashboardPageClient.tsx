"use client";

import { useEffect, useState } from "react";
import { endRouteProgress } from "@/lib/route-progress";
import { useAuth }         from "@/hooks/use-auth";
import { useNasdaqStocks } from "@/hooks/use-nasdaq-stocks";
import { useTutorial }     from "@/hooks/use-tutorial";
import { useKoreaInvestApiStatus } from "@/hooks/use-korea-invest-api-status";

import WorldIndicesTicker         from "@/components/dashboard/WorldIndicesTicker";
import RecommendStocksCards       from "@/components/dashboard/RecommendStocksCards";
import { MarketOverviewCard }     from "@/components/dashboard/MarketOverviewCard";
import { EconomicCalendarCard }   from "@/components/dashboard/EconomicCalendarCard";
import { MarketRiskPremiumCard }  from "@/components/dashboard/MarketRiskPremiumCard";
import { TutorialOverlay }        from "@/components/tutorial/tutorial-overlay";
import KoreaInvestApiRequired     from "@/components/KoreaInvestApiRequired";

/* ────────── 가시 종목 ────────── */
const INDEX = ["QQQ", "TQQQ", "ZM"];
const PORTF = ["005930", "000660", "051910"];

export default function DashboardPageClient() {
  const { accessTokenReady } = useAuth();
  const { isConfigured, isLoading, error } = useKoreaInvestApiStatus();
  
  // 디버깅: 현재 상태 출력
  console.log("🔍 [DashboardPageClient] 디버깅 정보:", {
    isConfigured,
    isLoading,
    error,
    isConfiguredType: typeof isConfigured,
    isConfiguredValue: isConfigured
  });

  // API가 설정되지 않았으면 다른 훅들을 실행하지 않음
  const { initWs, addSymbol, getStock, subscribeStore } = useNasdaqStocks();
  /* ────────── 튜토리얼 훅 ────────── */
  const {
    currentTutorial, currentStep, currentStepInfo,
    nextStep, previousStep, skipTutorial,
  } = useTutorial();

  // ✅ 한번만 초기화 + 구독 (성공/실패 분기 추가)
  useEffect(() => {
    // API가 설정되지 않았으면 실행하지 않음
    if (!isConfigured) return;
    
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
  }, [accessTokenReady, initWs, addSymbol, isConfigured]);

  // ── 시세 상태 ───────────────────────────
  const [marketData, setMarketData] = useState<any[]>([]);
  const [portfolioItems, setPortfolioItems] = useState<any[]>([]);
  const [aiSignals] = useState<any[]>([
    { label:"삼성전자",      action:"매수", confidence:"92%", change:"+5.1%", reason:"기술적 돌파 + 실적 개선 기대" },
    { label:"LG에너지솔루션", action:"매도", confidence:"78%", change:"-5.6%", reason:"과매수 구간 + 수급 약화" },
  ]);

  // ✅ 스토어 변경 시 즉시 리렌더
  useEffect(() => {
    // API가 설정되지 않았으면 실행하지 않음
    if (!isConfigured) return;
    
    const recompute = () => {
      // 실제 데이터가 있는 티커들만 필터링
      const activeTickers = INDEX.filter(symbol => {
        const stockInfo = getStock(symbol);
        return stockInfo && stockInfo.price > 0;
      });
      
      setMarketData(
        activeTickers.map((s) => {
          const info = getStock(s);
          return {
            label: s,
            value: info?.price ?? 0,
            change: info
              ? `${info.changePct >= 0 ? "+" : ""}${(info.changePct ?? 0).toFixed(2)}%`
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
    const unsubscribe = subscribeStore(recompute);
    // 초기 구독과 첫 데이터 가공이 끝난 시점에 진행바 종료
    // 실시간 WS 초기화(initWs)도 별도 effect에서 수행되며 성공 시 곧바로 데이터가 들어옴
    endRouteProgress();
    return unsubscribe;
  }, [getStock, subscribeStore, isConfigured]);

  /* ────────── 튜토리얼 훅 ────────── */
  // const {
  //   currentTutorial, currentStep, currentStepInfo,
  //   nextStep, previousStep, skipTutorial,
  // } = useTutorial();

  // 한국투자증권 API 설정이 안 되어 있다면 설명 페이지 표시
  if (!isConfigured) {
    console.log("🔍 [DashboardPageClient] !isConfigured 조건 실행됨 - KoreaInvestApiRequired 렌더링");
    return (
      <div className="w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
        <KoreaInvestApiRequired pageType="dashboard" />
      </div>
    );
  }

  if (isLoading) {
    console.log("🔍 [DashboardPageClient] isLoading 조건 실행됨");
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-300">API 설정 상태를 확인하는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    console.log("🔍 [DashboardPageClient] error 조건 실행됨");
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">오류가 발생했습니다: {error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  console.log("🔍 [DashboardPageClient] 정상 대시보드 렌더링");

  /* ────────── UI ────────── */
  return (
    <div className="w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
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
            <MarketOverviewCard markets={marketData} />
            <EconomicCalendarCard />
            <MarketRiskPremiumCard signals={aiSignals} />
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
