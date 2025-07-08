"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { XMarkIcon, ArrowRightIcon, ArrowLeftIcon, EyeIcon, HandRaisedIcon } from "@heroicons/react/24/outline"

const tutorialSteps = [
  {
    id: 1,
    title: "기가 버핏 시작하기",
    description: "AI 투자 플랫폼의 핵심 기능들을 단계별로 알아보겠습니다.",
    page: "dashboard",
    position: "top-right",
    details: [
      "💰 실시간 포트폴리오 가치 추적",
      "📊 수익률과 손익 현황 확인",
      "🚨 중요한 시장 알림 수신",
      "📈 성과 차트로 투자 성과 분석",
    ],
    actionTip: "상단 카드들을 클릭해서 상세 정보를 확인해보세요!",
    highlight: ".dashboard-content",
  },
  {
    id: 2,
    title: "포트폴리오 요약 카드",
    description: "투자 현황을 한눈에 파악할 수 있는 핵심 지표들입니다.",
    page: "dashboard",
    position: "top-left",
    details: [
      "🏦 총 자산: 현재 포트폴리오의 전체 가치",
      "📈 총 수익: 투자 원금 대비 수익/손실",
      "💵 현금: 투자 가능한 여유 자금",
      "📋 보유 종목: 현재 투자 중인 종목 수",
    ],
    actionTip: "각 카드를 클릭하면 더 자세한 분석을 볼 수 있어요.",
    highlight: ".tutorial-target-portfolio-cards",
  },
  {
    id: 3,
    title: "성과 차트 분석",
    description: "시각적 차트로 투자 성과와 자산 배분을 확인하세요.",
    page: "dashboard",
    position: "bottom-right",
    details: [
      "📊 포트폴리오 성과: 시간별 가치 변화 추이",
      "🥧 자산 배분: 종목별 투자 비중 확인",
      "📅 기간별 수익률: 일/주/월/년 단위 성과",
      "🔄 리밸런싱 신호: 자산 배분 조정 시점",
    ],
    actionTip: "차트 위에 마우스를 올려보면 상세 데이터를 볼 수 있어요.",
    highlight: ".tutorial-target-charts",
  },
  {
    id: 4,
    title: "시장 정보 센터",
    description: "실시간 시장 동향과 주요 종목 정보를 확인하세요.",
    page: "dashboard",
    position: "bottom-left",
    details: [
      "🚨 시장 알림: 중요한 시장 변동 소식",
      "📰 뉴스 업데이트: 투자 관련 최신 뉴스",
      "⭐ 주요 종목: 관심 종목의 실시간 가격",
      "📊 시장 지수: 코스피, 나스닥 등 주요 지수",
    ],
    actionTip: "알림을 클릭하면 관련 뉴스나 상세 정보를 볼 수 있어요.",
    highlight: ".tutorial-target-market",
  },
  {
    id: 5,
    title: "포트폴리오 상세 관리",
    description: "이제 포트폴리오 섹션에서 투자를 직접 관리해보겠습니다.",
    page: "portfolio",
    position: "top-right",
    details: [
      "📋 보유 종목 상세 정보 및 수익률",
      "💹 매수/매도 주문 실행",
      "⚖️ 포트폴리오 리밸런싱",
      "📊 종목별 성과 분석 및 비교",
    ],
    actionTip: "종목 행을 클릭하면 상세 정보와 거래 옵션을 볼 수 있어요.",
    highlight: null,
  },
  {
    id: 6,
    title: "종목 거래 및 분석",
    description: "개별 종목의 상세 정보와 거래 기능을 활용하세요.",
    page: "portfolio",
    position: "bottom-right",
    details: [
      "📈 실시간 주가 및 변동률 확인",
      "💰 평균 매수가 vs 현재가 비교",
      "🎯 목표가 설정 및 알림",
      "📊 기술적 분석 지표 활용",
    ],
    actionTip: "테이블에서 'View' 버튼을 클릭해서 종목 상세 정보를 확인해보세요.",
    highlight: ".tutorial-target-holdings-table",
  },
  {
    id: 7,
    title: "AI 투자 상담사",
    description: "24/7 AI 전문가와 투자 상담을 받아보세요.",
    page: "ai-chat",
    position: "top-left",
    details: [
      "🤖 개인 맞춤형 투자 조언 제공",
      "📊 시장 분석 및 종목 추천",
      "💡 투자 전략 수립 도움",
      "📚 투자 교육 및 용어 설명",
    ],
    actionTip: "하단의 제안 질문을 클릭하거나 직접 질문을 입력해보세요.",
    highlight: null,
  },
  {
    id: 8,
    title: "AI 채팅 활용법",
    description: "AI와 효과적으로 소통하는 방법을 알아보세요.",
    page: "ai-chat",
    position: "bottom-right",
    details: [
      "💬 구체적인 질문으로 정확한 답변 받기",
      "📋 대화 요약 기능으로 핵심 정보 정리",
      "🎯 투자 목표에 맞는 맞춤형 조언",
      "📈 실시간 시장 데이터 기반 분석",
    ],
    actionTip: "예시: '초보자를 위한 안전한 투자 방법을 알려주세요'라고 물어보세요.",
    highlight: ".tutorial-target-chat-input",
  },
  {
    id: 9,
    title: "개인 설정 관리",
    description: "투자 환경을 개인 취향에 맞게 설정하세요.",
    page: "settings",
    position: "top-right",
    details: [
      "👤 투자 성향 및 위험 선호도 설정",
      "🔔 알림 설정: 가격 변동, 뉴스, 목표 달성",
      "🔒 보안 설정: 2단계 인증, 비밀번호",
      "🎨 화면 테마 및 레이아웃 커스터마이징",
    ],
    actionTip: "각 설정 카드를 클릭해서 상세 옵션을 확인해보세요.",
    highlight: ".max-w-4xl",
  },
  {
    id: 10,
    title: "튜토리얼 완료! 🎉",
    description: "기가 버핏의 모든 핵심 기능을 둘러보셨습니다!",
    page: "dashboard",
    position: "center",
    details: [
      "🚀 이제 실제 투자를 시작해보세요",
      "💡 궁금한 점은 언제든 AI 채팅에서 질문",
      "📊 정기적으로 포트폴리오 점검",
      "🎯 투자 목표 달성을 위해 꾸준히 학습",
    ],
    actionTip: "성공적인 투자를 위해 기가 버핏과 함께 시작하세요!",
    highlight: null,
  },
]

interface DetailedGuideTutorialProps {
  onComplete: () => void
  onPageChange: (page: string) => void
  userProfile: any
  currentPage: string
}

export default function DetailedGuideTutorial({
  onComplete,
  onPageChange,
  userProfile,
  currentPage,
}: DetailedGuideTutorialProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [spotlightRect, setSpotlightRect] = useState<DOMRect | null>(null)

  useEffect(() => {
    if (currentStep === 0) {
      onPageChange("dashboard")
    }
  }, [])

  useEffect(() => {
    const step = tutorialSteps[currentStep]
    if (step && step.page !== currentPage) {
      setIsTransitioning(true)
      onPageChange(step.page)
      setTimeout(() => {
        setIsTransitioning(false)
        applySpotlight()
      }, 500)
    } else {
      setTimeout(() => applySpotlight(), 100)
    }
  }, [currentStep, onPageChange, currentPage])

  const applySpotlight = () => {
    const step = tutorialSteps[currentStep]
    if (step.highlight) {
      const element = document.querySelector(step.highlight)
      if (element) {
        const rect = element.getBoundingClientRect()
        setSpotlightRect(rect)
      } else {
        setSpotlightRect(null)
      }
    } else {
      setSpotlightRect(null)
    }
  }

  const handleSkip = () => {
    setSpotlightRect(null)
    onComplete()
  }

  const handleNext = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      setSpotlightRect(null)
      onComplete()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const currentTutorial = tutorialSteps[currentStep]
  const progress = ((currentStep + 1) / tutorialSteps.length) * 100

  const getPositionClasses = () => {
    if (isMinimized) return "bottom-4 right-4 w-64"

    switch (currentTutorial.position) {
      case "top-left":
        return "top-4 left-4 w-80"
      case "top-right":
        return "top-4 right-4 w-80"
      case "bottom-left":
        return "bottom-4 left-4 w-80"
      case "bottom-right":
        return "bottom-4 right-4 w-80"
      case "center":
        return "top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96"
      default:
        return "bottom-4 right-4 w-80"
    }
  }

  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      {/* 스포트라이트 오버레이 */}
      <div className="absolute inset-0 bg-black bg-opacity-60 transition-all duration-500">
        {spotlightRect && (
          <div
            className="absolute bg-transparent transition-all duration-500"
            style={{
              left: spotlightRect.left - 20,
              top: spotlightRect.top - 20,
              width: spotlightRect.width + 40,
              height: spotlightRect.height + 40,
              boxShadow: `
                0 0 0 20px rgba(0, 0, 0, 0.6),
                0 0 0 9999px rgba(0, 0, 0, 0.6),
                inset 0 0 0 3px rgba(59, 130, 246, 0.8),
                0 0 30px rgba(59, 130, 246, 0.5)
              `,
              borderRadius: "12px",
              animation: "spotlight-pulse 2s ease-in-out infinite",
            }}
          />
        )}
      </div>

      {/* 스포트라이트 애니메이션 */}
      <style jsx>{`
        @keyframes spotlight-pulse {
          0%, 100% {
            box-shadow: 
              0 0 0 20px rgba(0, 0, 0, 0.6),
              0 0 0 9999px rgba(0, 0, 0, 0.6),
              inset 0 0 0 3px rgba(59, 130, 246, 0.8),
              0 0 30px rgba(59, 130, 246, 0.5);
          }
          50% {
            box-shadow: 
              0 0 0 20px rgba(0, 0, 0, 0.6),
              0 0 0 9999px rgba(0, 0, 0, 0.6),
              inset 0 0 0 4px rgba(59, 130, 246, 1),
              0 0 40px rgba(59, 130, 246, 0.8);
          }
        }
      `}</style>

      {/* 튜토리얼 카드 */}
      <div className={`absolute ${getPositionClasses()} pointer-events-auto transition-all duration-300`}>
        <Card className="shadow-2xl border-2 border-blue-400 bg-white/95 backdrop-blur-sm">
          <CardContent className={`${isMinimized ? "p-2" : "p-3"}`}>
            {/* 헤더 */}
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className={`${isMinimized ? "text-xs" : "text-sm"} font-bold text-gray-900`}>
                    {currentTutorial.title}
                  </h3>
                  {isTransitioning && (
                    <div className="animate-spin rounded-full h-2 w-2 border-b-2 border-blue-500"></div>
                  )}
                </div>
                {!isMinimized && <p className="text-gray-600 text-xs mb-1">{currentTutorial.description}</p>}
              </div>
              <div className="flex space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="text-gray-400 hover:text-gray-600 p-0.5 h-6 w-6"
                >
                  <EyeIcon className="w-3 h-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSkip}
                  className="text-gray-400 hover:text-gray-600 p-0.5 h-6 w-6"
                >
                  <XMarkIcon className="w-3 h-3" />
                </Button>
              </div>
            </div>

            {!isMinimized && (
              <>
                {/* 상세 내용 */}
                <div className="mb-3">
                  <div className="space-y-1 mb-2">
                    {currentTutorial.details.map((detail, index) => (
                      <div key={index} className="flex items-start space-x-1.5">
                        <div className="w-1 h-1 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                        <p className="text-xs text-gray-700 leading-relaxed">{detail}</p>
                      </div>
                    ))}
                  </div>

                  {/* 액션 팁 */}
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-2 border border-blue-200">
                    <div className="flex items-start space-x-1.5">
                      <HandRaisedIcon className="w-3 h-3 text-blue-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-blue-800 font-medium">{currentTutorial.actionTip}</p>
                    </div>
                  </div>

                  {/* 개인화된 팁 */}
                  {currentStep === 1 && userProfile?.experience === "beginner" && (
                    <div className="mt-1.5 p-1.5 bg-green-50 rounded-lg border border-green-200">
                      <p className="text-xs text-green-800">
                        💡 초보자 팁: 처음에는 총 자산과 수익률 카드부터 확인해보세요!
                      </p>
                    </div>
                  )}

                  {currentStep === 4 && userProfile?.investmentStyle === "longterm" && (
                    <div className="mt-1.5 p-1.5 bg-purple-50 rounded-lg border border-purple-200">
                      <p className="text-xs text-purple-800">
                        💡 장기투자자 팁: 포트폴리오에서 분산투자 비율을 정기적으로 확인하세요!
                      </p>
                    </div>
                  )}

                  {currentStep === 6 && userProfile?.riskTolerance === "conservative" && (
                    <div className="mt-1.5 p-1.5 bg-orange-50 rounded-lg border border-orange-200">
                      <p className="text-xs text-orange-800">
                        💡 보수적 투자자 팁: AI에게 "안전한 배당주 추천"을 요청해보세요!
                      </p>
                    </div>
                  )}
                </div>

                {/* 진행률 */}
                <div className="mb-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>
                      {currentStep + 1} / {tutorialSteps.length}
                    </span>
                    <span>{Math.round(progress)}% 완료</span>
                  </div>
                  <Progress value={progress} className="h-1" />
                </div>
              </>
            )}

            {/* 네비게이션 버튼 */}
            <div className={`flex justify-between items-center ${isMinimized ? "mt-1" : ""}`}>
              <Button
                variant="outline"
                onClick={handlePrev}
                disabled={currentStep === 0}
                size="sm"
                className="flex items-center space-x-1 bg-transparent text-xs h-7 px-2"
              >
                <ArrowLeftIcon className="w-3 h-3" />
                <span>이전</span>
              </Button>

              {!isMinimized && (
                <div className="flex space-x-1">
                  {tutorialSteps.map((_, index) => (
                    <div
                      key={index}
                      className={`w-1 h-1 rounded-full transition-colors ${
                        index === currentStep ? "bg-blue-500" : "bg-gray-300"
                      }`}
                    />
                  ))}
                </div>
              )}

              <Button
                onClick={handleNext}
                disabled={isTransitioning}
                size="sm"
                className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white flex items-center space-x-1 text-xs h-7 px-2"
              >
                <span>{currentStep === tutorialSteps.length - 1 ? "완료" : "다음"}</span>
                {currentStep !== tutorialSteps.length - 1 && <ArrowRightIcon className="w-3 h-3" />}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 현재 페이지 표시 (최소화 시에만) */}
      {isMinimized && (
        <div className="absolute top-4 right-4 pointer-events-auto">
          <div className="bg-white/90 backdrop-blur rounded-lg px-2 py-1 border border-gray-200 text-xs">
            <span className="text-gray-600">현재: </span>
            <span className="text-blue-600 font-medium">
              {currentTutorial.page === "dashboard"
                ? "대시보드"
                : currentTutorial.page === "portfolio"
                  ? "포트폴리오"
                  : currentTutorial.page === "ai-chat"
                    ? "AI 채팅"
                    : "설정"}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
