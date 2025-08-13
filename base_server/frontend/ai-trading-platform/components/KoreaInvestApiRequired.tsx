"use client";

import { useRouter } from "next/navigation";
import { Settings, BarChart3, PieChart, AlertTriangle, MessageSquare, TrendingUp, Zap, CheckCircle, ArrowRight, Sparkles, Shield, Target } from "lucide-react";

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
      features: [
        "실시간 주식 시세 및 시장 동향 모니터링",
        "AI 분석 기반 투자 추천 및 신호 제공",
        "글로벌 시장 지수 및 섹터별 성과 분석"
      ]
    },
    portfolio: {
      title: "포트폴리오",
      description: "투자 포트폴리오 현황과 성과를 분석할 수 있는 페이지",
      icon: PieChart,
      features: [
        "보유 종목별 실시간 수익률 및 손익 현황",
        "포트폴리오 성과 분석 및 리스크 평가",
        "자산 분산 및 투자 전략 최적화"
      ]
    },
  };

  const currentPage = pageInfo[pageType];
  const IconComponent = currentPage.icon;

  const handleGoToSettings = () => {
    router.push("/settings");
  };

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-black via-gray-900 to-gray-800 text-white relative overflow-hidden">
      {/* 배경 효과 */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(0,100,200,0.1)_0%,transparent_50%),radial-gradient(circle_at_80%_20%,rgba(255,255,255,0.05)_0%,transparent_50%),radial-gradient(circle_at_40%_40%,rgba(0,50,150,0.08)_0%,transparent_50%)]"></div>
      
      {/* 그리드 패턴 */}
      <div className="absolute inset-0 bg-[repeating-linear-gradient(90deg,transparent,transparent_2px,rgba(255,255,255,0.01)_2px,rgba(255,255,255,0.01)_4px),repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(255,255,255,0.01)_2px,rgba(255,255,255,0.01)_4px)] pointer-events-none"></div>
      
      {/* 애니메이션 배경 */}
      <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_30%,rgba(102,126,234,0.02)_50%,transparent_70%),linear-gradient(-45deg,transparent_30%,rgba(118,75,162,0.02)_50%,transparent_70%)] animate-background-shift"></div>

      <main className="relative z-10 flex flex-col items-center justify-center px-6 md:px-12 py-8 pt-16">
        <div className="max-w-6xl mx-auto text-center">
          
          {/* 1. 메인 헤더 섹션 */}
          <div className="mb-12 animate-fade-in">
            <div className="relative mb-8">
              {/* 경고 아이콘 */}
              <div className="w-28 h-28 mx-auto bg-gradient-to-br from-yellow-400 via-orange-500 to-red-500 rounded-full flex items-center justify-center mb-6 shadow-2xl animate-pulse relative">
                <AlertTriangle size={56} className="text-white" />
                {/* 글로우 효과 */}
                <div className="absolute inset-0 bg-gradient-to-br from-yellow-400/20 to-red-500/20 rounded-full blur-xl animate-pulse"></div>
              </div>
              
              {/* 스파클 효과 */}
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full animate-bounce"></div>
              <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-orange-400 rounded-full animate-bounce" style={{animationDelay: '0.5s'}}></div>
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold mb-6 text-white leading-tight">
              한국투자증권 API 설정이{" "}
              <span className="bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
                필요합니다
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
              <span className="font-semibold text-white">{currentPage.title}</span> 페이지를 이용하려면 
              <span className="text-yellow-400 font-semibold"> 한국투자증권 API 설정</span>을 완료해야 합니다.
            </p>
          </div>

          {/* 2. 현재 이용 가능한 기능들 */}
          <div className="mb-20 animate-fade-in-up animation-delay-200">
            <div className="flex items-center justify-center gap-3 mb-12">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <CheckCircle size={20} className="text-white" />
              </div>
              <h2 className="text-4xl font-bold text-white">
                🎯 <span className="bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
                  현재 이용 가능한 기능들
                </span>
              </h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              {/* AI 시그널 카드 */}
              <div className="group relative">
                <div className="bg-gradient-to-br from-green-500/20 to-emerald-600/20 backdrop-blur-sm rounded-2xl p-8 border border-green-500/30 hover:border-green-400/50 transition-all duration-500 transform hover:scale-105 hover:shadow-2xl hover:shadow-green-500/20">
                  <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg">
                        <TrendingUp size={32} className="text-white" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-white">AI 시그널</h3>
                        <p className="text-green-200 text-sm">실시간 투자 신호</p>
                      </div>
                    </div>
                    <p className="text-green-100 text-lg leading-relaxed">
                      AI가 분석한 투자 신호와 자동매매 전략을 확인할 수 있습니다
                    </p>
                  </div>
                  
                  {/* 호버 시 글로우 효과 */}
                  <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl"></div>
                </div>
              </div>
              
              {/* AI 챗봇 카드 */}
              <div className="group relative">
                <div className="bg-gradient-to-br from-blue-500/20 to-indigo-600/20 backdrop-blur-sm rounded-2xl p-8 border border-blue-500/30 hover:border-blue-400/50 transition-all duration-500 transform hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/20">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
                        <MessageSquare size={32} className="text-white" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-white">AI 챗봇</h3>
                        <p className="text-blue-200 text-sm">투자 상담 서비스</p>
                      </div>
                    </div>
                    <p className="text-blue-100 text-lg leading-relaxed">
                      투자 관련 질문에 대해 AI가 답변하고 조언을 제공합니다
                    </p>
                  </div>
                  
                  {/* 호버 시 글로우 효과 */}
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl"></div>
                </div>
              </div>
            </div>
            
            {/* 안내 메시지 */}
            <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 backdrop-blur-sm rounded-2xl p-6 border border-green-500/20 max-w-2xl mx-auto">
              <div className="flex items-center justify-center gap-3 text-green-300">
                <Sparkles size={20} className="text-green-400" />
                <p className="text-lg">
                  <strong className="text-white">헤더의 사이드바 메뉴</strong>를 클릭하여 위 기능들을 바로 이용할 수 있습니다!
                </p>
              </div>
            </div>
          </div>

          {/* 3. 대시보드/포트폴리오 소개 */}
          <div className="mb-20 animate-fade-in-up animation-delay-300">
            <div className="flex items-center justify-center gap-3 mb-12">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <Target size={20} className="text-white" />
              </div>
              <h2 className="text-4xl font-bold text-white">
                📊 <span className="bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                  {currentPage.title} 페이지 소개
                </span>
              </h2>
            </div>
            
            <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-3xl p-10 border border-white/20 shadow-2xl max-w-4xl mx-auto">
              <div className="flex items-center gap-6 mb-8">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl">
                  <IconComponent size={40} className="text-white" />
                </div>
                <div className="text-left">
                  <h3 className="text-3xl font-bold text-white mb-2">{currentPage.title}</h3>
                  <p className="text-gray-300 text-lg">{currentPage.description}</p>
                </div>
              </div>
              
              <div className="text-left space-y-4">
                {currentPage.features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-4 group">
                    <div className="w-3 h-3 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full mt-3 flex-shrink-0 group-hover:scale-125 transition-transform duration-300"></div>
                    <p className="text-gray-300 text-lg group-hover:text-white transition-colors duration-300">{feature}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 4. 왜 필요한지 설명 */}
          <div className="mb-20 animate-fade-in-up animation-delay-400">
            <div className="flex items-center justify-center gap-3 mb-12">
              <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                <Shield size={20} className="text-white" />
              </div>
              <h2 className="text-4xl font-bold text-white">
                <span className="bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                  왜 한국투자증권 API가 필요한가요?
                </span>
              </h2>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
              {/* 보안 및 인증 */}
              <div className="bg-gradient-to-br from-yellow-500/10 to-orange-500/10 backdrop-blur-sm rounded-2xl p-8 border border-yellow-500/20 hover:border-yellow-400/40 transition-all duration-300">
                <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                  <Shield size={28} className="text-yellow-400" />
                  보안 및 인증
                </h3>
                <div className="space-y-4 text-left">
                  {[
                    "개인 계좌 정보 보호 및 안전한 접근",
                    "공식 API를 통한 신뢰할 수 있는 데이터",
                    "실시간 시장 데이터의 정확성 보장"
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3 group">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full mt-3 flex-shrink-0 group-hover:scale-150 transition-transform duration-300"></div>
                      <p className="text-gray-300 group-hover:text-white transition-colors duration-300">{item}</p>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* 개인화된 서비스 */}
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-sm rounded-2xl p-8 border border-purple-500/20 hover:border-purple-400/40 transition-all duration-300">
                <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                  <Target size={28} className="text-purple-400" />
                  개인화된 서비스
                </h3>
                <div className="space-y-4 text-left">
                  {[
                    "본인 계좌 기반 맞춤형 포트폴리오 분석",
                    "실제 보유 종목 기반 AI 투자 신호",
                    "계좌별 수익률 및 성과 추적"
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3 group">
                      <div className="w-2 h-2 bg-purple-400 rounded-full mt-3 flex-shrink-0 group-hover:scale-150 transition-transform duration-300"></div>
                      <p className="text-gray-300 group-hover:text-white transition-colors duration-300">{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 5. 설정 페이지로 이동 */}
          <div className="animate-fade-in-up animation-delay-500">
            <div className="flex items-center justify-center gap-3 mb-8">
              <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                <Zap size={20} className="text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white">
                🚀 <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                  지금 바로 설정하세요!
                </span>
              </h2>
            </div>
            
            <div className="bg-gradient-to-r from-purple-500/20 via-blue-500/20 to-indigo-500/20 backdrop-blur-sm rounded-3xl p-10 border border-purple-500/30 shadow-2xl max-w-3xl mx-auto">
              <p className="text-gray-300 text-xl mb-8 leading-relaxed">
                한국투자증권 API 설정을 완료하면{" "}
                <strong className="text-white">{currentPage.title}</strong> 페이지를 포함한 모든 기능을{" "}
                <span className="bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent font-semibold">
                  무제한으로 이용
                </span>할 수 있습니다.
              </p>
              
              <button
                onClick={handleGoToSettings}
                className="group w-full md:w-auto px-12 py-6 bg-gradient-to-r from-purple-500 via-blue-600 to-indigo-600 hover:from-purple-600 hover:via-blue-700 hover:to-indigo-700 text-white font-bold text-xl rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/30 flex items-center justify-center gap-4 mx-auto"
              >
                <Settings size={28} className="group-hover:rotate-12 transition-transform duration-300" />
                설정 페이지로 이동
                <ArrowRight size={24} className="group-hover:translate-x-2 transition-transform duration-300" />
              </button>
              
              <p className="text-gray-400 mt-6 text-center">
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
            transform: translateY(40px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes backgroundShift {
          0%, 100% {
            transform: translateX(0) translateY(0);
            opacity: 1;
          }
          50% {
            transform: translateX(20px) translateY(-20px);
            opacity: 0.5;
          }
        }
        
        .animate-fade-in {
          animation: fadeIn 0.8s ease-out;
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.8s ease-out;
        }
        
        .animation-delay-200 {
          animation-delay: 0.2s;
        }
        
        .animation-delay-300 {
          animation-delay: 0.4s;
        }
        
        .animation-delay-400 {
          animation-delay: 0.6s;
        }
        
        .animation-delay-500 {
          animation-delay: 0.8s;
        }
        
        .animate-background-shift {
          animation: backgroundShift 20s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
} 