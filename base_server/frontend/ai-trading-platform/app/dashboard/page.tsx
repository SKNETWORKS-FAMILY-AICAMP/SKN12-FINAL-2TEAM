"use client"

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth"
import { useTutorial } from "@/hooks/use-tutorial"
import { TutorialOverlay } from "@/components/tutorial/tutorial-overlay"
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
import RecommendStocksCards from "@/components/dashboard/RecommendStocksCards";
import WorldIndicesTicker from "@/components/dashboard/WorldIndicesTicker";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const { 
    currentTutorial, 
    currentStep, 
    currentStepInfo, 
    nextStep, 
    previousStep, 
    skipTutorial 
  } = useTutorial();
                const [marketData, setMarketData] = useState([
                { label: "KOSPI", value: 0, change: "N/A" },
                { label: "S&P 500", value: 0, change: "N/A" },
                { label: "KOSDAQ", value: 0, change: "N/A" },
              ]);
  const [rawMarketData, setRawMarketData] = useState<any>(null);
                const [portfolioItems, setPortfolioItems] = useState([
                { label: "삼성전자", change: "N/A" },
                { label: "SK하이닉스", change: "N/A" },
                { label: "LG에너지솔루션", change: "N/A" },
              ]);
  const [aiSignals, setAiSignals] = useState([
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
  ]);
  const [isLoadingData, setIsLoadingData] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/auth/login");
    }
  }, [user, isLoading, router]);

                // 웹소켓 실시간 데이터 연결
              useEffect(() => {
                if (!user) {
                  console.log("사용자 정보 없음, 웹소켓 연결 중단");
                  return;
                }

                console.log("웹소켓 실시간 데이터 연결 시작");
                
                // 웹소켓 클라이언트 가져오기
                const { getWebSocketClient } = require('@/lib/websocket-client');
                const wsClient = getWebSocketClient();

                console.log('웹소켓 연결 시도...');
                
                // 웹소켓 연결
                wsClient.connect().then(() => {
                  console.log("웹소켓 연결 성공");
                  
                  // 시장 데이터 구독
                  wsClient.onMessage('market_data', (data: any) => {
                    console.log("웹소켓 시장 데이터 수신:", data);
                    if (data.market_data) {
                      setRawMarketData(data.market_data);
                      const newMarketData = [
                        { 
                          label: "KOSPI", 
                          value: data.market_data.kospi?.current_price || 0, 
                          change: data.market_data.kospi?.current_price ? `${data.market_data.kospi.change_rate > 0 ? '+' : ''}${data.market_data.kospi.change_rate}%` : "N/A"
                        },
                        { 
                          label: "S&P 500", 
                          value: data.market_data.sp500?.current_price || 0, 
                          change: data.market_data.sp500?.current_price ? `${data.market_data.sp500.change_rate > 0 ? '+' : ''}${data.market_data.sp500.change_rate}%` : "N/A"
                        },
                        { 
                          label: "KOSDAQ", 
                          value: data.market_data.kosdaq?.current_price || 0, 
                          change: data.market_data.kosdaq?.current_price ? `${data.market_data.kosdaq.change_rate > 0 ? '+' : ''}${data.market_data.kosdaq.change_rate}%` : "N/A"
                        },
                      ];
                      setMarketData(newMarketData);
                    }
                  });

                  // 포트폴리오 데이터 구독
                  wsClient.onMessage('portfolio_data', (data: any) => {
                    console.log("웹소켓 포트폴리오 데이터 수신:", data);
                    if (data.portfolio_data) {
                      const newPortfolioItems = data.portfolio_data.map((item: any) => {
                        const stockNames: { [key: string]: string } = {
                          '005930': '삼성전자',
                          '000660': 'SK하이닉스',
                          '051910': 'LG에너지솔루션'
                        };
                        const label = stockNames[item.symbol] || item.name || item.symbol;
                        return {
                          label: label,
                          change: `${item.change_rate > 0 ? '+' : ''}${item.change_rate}%`
                        };
                      });
                      setPortfolioItems(newPortfolioItems);
                    }
                  });

                  // 초기 데이터 요청
                  wsClient.send({
                    type: 'subscribe',
                    symbols: ['005930', '000660', '051910'],
                    indices: ['0001', '1001']
                  });

                }).catch((error: any) => {
                  console.error("웹소켓 연결 실패:", error);
                  // 연결 실패 시 N/A 표시
                  setMarketData([
                    { label: "KOSPI", value: 0, change: "N/A" },
                    { label: "S&P 500", value: 0, change: "N/A" },
                    { label: "KOSDAQ", value: 0, change: "N/A" },
                  ]);
                  setPortfolioItems([
                    { label: "삼성전자", change: "N/A" },
                    { label: "SK하이닉스", change: "N/A" },
                    { label: "LG에너지솔루션", change: "N/A" },
                  ]);
                });

                // 컴포넌트 언마운트 시 웹소켓 정리
                return () => {
                  console.log("웹소켓 연결 정리");
                  wsClient.offMessage('market_data');
                  wsClient.offMessage('portfolio_data');
                  // 연결은 유지 (다른 페이지에서도 사용할 수 있도록)
                };
              }, [user]);

  // 인증 상태 확인 중이거나, 유저가 없으면 로딩 화면이나 null을 반환
  if (isLoading || !user) {
    return (
      <div className="flex justify-center items-center h-screen">
        <p>Loading...</p>
      </div>
    );
  }

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

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
      <WorldIndicesTicker marketData={rawMarketData} />
      <main className="flex-1 flex flex-col items-center px-6 md:px-12 py-2 bg-transparent overflow-hidden">
        <h1 className="text-2xl md:text-3xl font-bold mb-2 tracking-tight text-white text-left w-full max-w-7xl">
          Professional <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">AI Trading Dashboard</span>
          {isLoadingData && <span className="ml-2 text-sm text-gray-400">실시간 업데이트 중...</span>}
        </h1>
        <div className="flex-1 flex flex-col items-center w-full">
          <RecommendStocksCards />
          <div className="w-full flex justify-center">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-2 max-w-7xl">
              <MarketOverviewCard markets={marketData} />
              <PortfolioBreakdownCard items={portfolioItems} />
              <AISignalCard signals={aiSignals} />
            </div>
          </div>
        </div>
      </main>
      {/* 튜토리얼 오버레이 */}
      <TutorialOverlay
        isVisible={!!currentTutorial && !!currentStepInfo()}
        stepInfo={currentStepInfo()}
        onNext={nextStep}
        onPrevious={previousStep}
        onSkip={skipTutorial}
        currentStep={currentStep}
        totalSteps={currentTutorial === 'OVERVIEW' ? 6 : 0}
      />
    </div>
  );
} 