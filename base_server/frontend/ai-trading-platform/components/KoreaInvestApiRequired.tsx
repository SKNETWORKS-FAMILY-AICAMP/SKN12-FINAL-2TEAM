"use client";

import { useRouter } from "next/navigation";
import { Settings, BarChart3, PieChart, AlertTriangle, MessageSquare, TrendingUp, Zap, CheckCircle } from "lucide-react";

interface KoreaInvestApiRequiredProps {
  pageType: "dashboard" | "portfolio";
}

export default function KoreaInvestApiRequired({ pageType }: KoreaInvestApiRequiredProps) {
  const router = useRouter();
  
  const pageInfo = {
    dashboard: {
      title: "대시보드",
      description: "실시간 시장 데이터와 AI 신호를 확인할 수 있는 대시보드",
      icon: BarChart3,
    },
    portfolio: {
      title: "포트폴리오",
      description: "투자 포트폴리오 현황과 성과를 분석할 수 있는 페이지",
      icon: PieChart,
    },
  };

  const currentPage = pageInfo[pageType];
  const IconComponent = currentPage.icon;

  const handleGoToSettings = () => {
    router.push("/settings");
  };

  return (
    <div className="w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
      <main className="flex flex-col items-center justify-center px-6 md:px-12 py-8">
        <div className="max-w-4xl mx-auto text-center">
          {/* Warning 아이콘과 설명 */}
          <div className="mb-8 animate-fade-in">
            <div className="w-24 h-24 mx-auto bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mb-6 shadow-2xl animate-pulse">
              <AlertTriangle size={48} className="text-white" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-6 text-white">
              한국투자증권 API 설정이 필요합니다
            </h1>
            <p className="text-lg text-gray-300 mb-6">
              <span className="font-semibold text-white">{currentPage.title}</span> 페이지를 이용하려면 한국투자증권 API 설정을 완료해야 합니다.
            </p>
          </div>

          {/* 1. 현재 이용 가능한 기능들 */}
          <div className="mb-12 animate-fade-in-up animation-delay-200">
            <h2 className="text-3xl font-bold text-white mb-8">
              🎯 <span className="text-green-400">현재 이용 가능한 기능들</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-green-500/20 backdrop-blur-sm rounded-lg p-6 border border-green-500/30 hover:bg-green-500/30 transition-all duration-300">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                    <TrendingUp size={24} className="text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">AI 시그널</h3>
                </div>
                <p className="text-green-200">AI가 분석한 투자 신호와 자동매매 전략을 확인할 수 있습니다</p>
              </div>
              
              <div className="bg-blue-500/20 backdrop-blur-sm rounded-lg p-6 border border-blue-500/30 hover:bg-blue-500/30 transition-all duration-300">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                    <MessageSquare size={24} className="text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">AI 챗봇</h3>
                </div>
                <p className="text-blue-200">투자 관련 질문에 대해 AI가 답변하고 조언을 제공합니다</p>
              </div>
            </div>
            
            <div className="bg-green-500/10 backdrop-blur-sm rounded-lg p-4 border border-green-500/20">
              <p className="text-green-300">
                💡 <strong>헤더의 햄버거 메뉴</strong>를 클릭하여 위 기능들을 바로 이용할 수 있습니다!
              </p>
            </div>
          </div>

          {/* 2. 대시보드/포트폴리오가 어떤 페이지인지 설명 */}
          <div className="mb-12 animate-fade-in-up animation-delay-300">
            <h2 className="text-3xl font-bold text-white mb-8">
              📊 <span className="text-blue-400">{currentPage.title} 페이지 소개</span>
            </h2>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8 border border-white/20 shadow-xl">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
                  <IconComponent size={32} className="text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">{currentPage.title}</h3>
                  <p className="text-gray-300">{currentPage.description}</p>
                </div>
              </div>
              
              <div className="text-left space-y-4 text-gray-300">
                {pageType === "dashboard" ? (
                  <>
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                      <p>실시간 주식 시세 및 시장 동향 모니터링</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                      <p>AI 분석 기반 투자 추천 및 신호 제공</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                      <p>글로벌 시장 지수 및 섹터별 성과 분석</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                      <p>보유 종목별 실시간 수익률 및 손익 현황</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                      <p>포트폴리오 성과 분석 및 리스크 평가</p>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                      <p>자산 분산 및 투자 전략 최적화</p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* 3. 왜 필요한지 설명 */}
          <div className="mb-12 bg-white/5 backdrop-blur-sm rounded-lg p-8 border border-white/10 shadow-xl animate-fade-in-up animation-delay-400">
            <h2 className="text-3xl font-bold text-white mb-8">
              ❓ <span className="text-yellow-400">왜 한국투자증권 API가 필요한가요?</span>
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-white mb-4">🔐 보안 및 인증</h3>
                <div className="space-y-3 text-gray-300">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                    <p>개인 계좌 정보 보호 및 안전한 접근</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                    <p>공식 API를 통한 신뢰할 수 있는 데이터</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                    <p>실시간 시장 데이터의 정확성 보장</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-white mb-4">📈 개인화된 서비스</h3>
                <div className="space-y-3 text-gray-300">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                    <p>본인 계좌 기반 맞춤형 포트폴리오 분석</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                    <p>실제 보유 종목 기반 AI 투자 신호</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                    <p>계좌별 수익률 및 성과 추적</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 4. 설정 페이지로 리다이렉트 */}
          <div className="animate-fade-in-up animation-delay-500">
            <h2 className="text-2xl font-bold text-white mb-6">
              🚀 <span className="text-purple-400">지금 바로 설정하세요!</span>
            </h2>
            
            <div className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 backdrop-blur-sm rounded-lg p-6 border border-purple-500/30 shadow-xl">
              <p className="text-gray-300 mb-6">
                한국투자증권 API 설정을 완료하면 <strong className="text-white">{currentPage.title}</strong> 페이지를 포함한 모든 기능을 
                <span className="text-green-400 font-semibold"> 무제한으로 이용</span>할 수 있습니다.
              </p>
              
              <button
                onClick={handleGoToSettings}
                className="w-full md:w-auto px-10 py-5 bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 text-white font-semibold text-lg rounded-lg transition-all duration-200 transform hover:scale-105 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl"
              >
                <Settings size={24} />
                설정 페이지로 이동
              </button>
              
              <p className="text-sm text-gray-400 mt-4">
                설정 완료 후 다시 접근하시면 정상적으로 이용할 수 있습니다.
              </p>
            </div>
          </div>
        </div>
      </main>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fadeIn 0.6s ease-out;
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.6s ease-out;
        }
        
        .animation-delay-200 {
          animation-delay: 0.2s;
        }
        
        .animation-delay-300 {
          animation-delay: 0.3s;
        }
        
        .animation-delay-400 {
          animation-delay: 0.4s;
        }
        
        .animation-delay-500 {
          animation-delay: 0.5s;
        }
      `}</style>
    </div>
  );
} 