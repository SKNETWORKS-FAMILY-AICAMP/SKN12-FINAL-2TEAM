"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { ArrowRightIcon, ArrowLeftIcon } from "@heroicons/react/24/outline"

const tutorialSteps = [
  {
    id: 1,
    title: "기가 버핏에 오신 것을 환영합니다! 🎉",
    page: "dashboard",
    target: ".dashboard-content",
    position: "center",
    content:
      "AI와 함께하는 스마트한 투자 플랫폼입니다. 실시간 포트폴리오 관리, AI 투자 상담, 자동매매까지 모든 투자 도구를 한 곳에서 이용하세요.",
    details:
      "• 실시간 투자 현황 모니터링\n• AI 기반 개인 맞춤 투자 조언\n• 자동화된 포트폴리오 관리\n• 24/7 시장 분석 및 알림",
    highlight: false,
    isMainSection: true,
  },
  {
    id: 2,
    title: "대시보드 - 투자 현황 한눈에 📊",
    page: "dashboard",
    target: null,
    position: "center",
    content:
      "대시보드는 투자의 중심입니다. 모든 투자 정보를 실시간으로 확인하고, 시장 동향을 파악할 수 있는 메인 허브입니다. 직관적인 차트와 카드로 복잡한 투자 데이터를 쉽게 이해할 수 있어요.",
    details:
      "• 포트폴리오 요약: 총 자산, 수익률, 현금 현황\n• 성과 차트: 시간별 가치 변화와 자산 배분\n• 시장 알림: 중요한 시장 변동 실시간 알림\n• 주요 종목: 관심 종목 가격 모니터링\n• 투자 인사이트: AI 기반 시장 분석",
    highlight: false,
    isMainSection: true,
  },
  {
    id: 3,
    title: "포트폴리오 카드",
    page: "dashboard",
    target: ".portfolio-cards",
    position: "bottom",
    content: "총 자산, 수익률, 현금을 확인하세요.",
    details: "",
    highlight: true,
    isMainSection: false,
  },
  {
    id: 4,
    title: "성과 차트",
    page: "dashboard",
    target: ".performance-chart",
    position: "left",
    content: "포트폴리오 성과와 자산 배분을 확인하세요.",
    details: "",
    highlight: true,
    isMainSection: false,
  },
  {
    id: 5,
    title: "포트폴리오 - 투자 관리의 핵심 💼",
    page: "portfolio",
    target: null,
    position: "center",
    content:
      "포트폴리오 섹션은 전문적인 투자 관리를 위한 핵심 도구입니다. 보유 종목의 상세 분석부터 매매 실행까지, 모든 투자 활동을 체계적으로 관리할 수 있습니다. 실시간 데이터와 AI 분석으로 최적의 투자 결정을 내리세요.",
    details:
      "• 보유 종목 관리: 실시간 가격, 수익률, 손익 현황\n• 매매 실행: 원클릭 매수/매도 주문\n• 포트폴리오 분석: 성과 평가 및 리스크 분석\n• 리밸런싱: 자동 자산 배분 조정\n• 투자 목표: 목표 설정 및 달성도 추적",
    highlight: false,
    isMainSection: true,
  },
  {
    id: 6,
    title: "종목 테이블",
    page: "portfolio",
    target: "table",
    position: "top",
    content: "보유 종목의 상세 정보를 확인하고 거래하세요.",
    details: "",
    highlight: true,
    isMainSection: false,
  },
  {
    id: 7,
    title: "AI 채팅 - 24/7 투자 상담사 🤖",
    page: "ai-chat",
    target: null,
    position: "center",
    content:
      "AI 채팅은 당신만의 개인 투자 상담사입니다. 워렌 버핏, 피터 린치 등 유명 투자자의 철학을 학습한 AI가 24시간 언제든지 맞춤형 조언을 제공합니다. 복잡한 투자 개념도 쉽게 설명해드려요.",
    details:
      "• 개인 맞춤 상담: 투자 성향에 맞는 조언\n• 투자자 페르소나: 다양한 투자 철학 선택\n• 실시간 분석: 시장 데이터 기반 즉시 답변\n• 투자 교육: 용어 설명과 개념 학습\n• 전략 수립: 투자 계획 및 목표 설정 도움",
    highlight: false,
    isMainSection: true,
  },
  {
    id: 8,
    title: "채팅 입력창",
    page: "ai-chat",
    target: ".tutorial-target-chat-input",
    position: "top",
    content: "투자 질문을 입력하거나 제안 질문을 클릭하세요.",
    details: "",
    highlight: true,
    isMainSection: false,
  },
  {
    id: 9,
    title: "자동매매 - AI 투자 전략 ⚡",
    page: "auto-trading",
    target: null,
    position: "center",
    content:
      "자동매매는 감정에 휘둘리지 않는 체계적인 투자를 가능하게 합니다. AI와 대화하여 개인 맞춤형 투자 전략을 생성하고, 24시간 자동으로 거래를 실행합니다. 백테스팅과 실시간 모니터링으로 안전하게 관리됩니다.",
    details:
      "• 전략 생성: AI와 대화로 맞춤형 전략 개발\n• 자동 실행: 24/7 무인 거래 시스템\n• 리스크 관리: 손절매, 익절매 자동 설정\n• 성과 추적: 실시간 수익률 및 거래 내역\n• 백테스팅: 과거 데이터로 전략 검증",
    highlight: false,
    isMainSection: true,
  },
  {
    id: 10,
    title: "설정 - 개인화 관리 ⚙️",
    page: "settings",
    target: null,
    position: "center",
    content:
      "설정에서 기가 버핏을 완전히 개인화하세요. 투자 성향부터 알림 설정, 보안까지 모든 것을 세밀하게 조정할 수 있습니다. 당신만의 투자 환경을 만들어 더 효율적이고 안전한 투자를 경험하세요.",
    details:
      "• 투자 프로필: 경험, 성향, 목표 설정\n• 알림 관리: 가격, 뉴스, 포트폴리오 알림\n• 보안 강화: 2단계 인증, 생체 인증\n• 화면 설정: 테마, 언어, 차트 스타일\n• 구독 관리: 플랜 업그레이드 및 결제",
    highlight: false,
    isMainSection: true,
  },
  {
    id: 11,
    title: "설정 카드들",
    page: "settings",
    target: ".max-w-7xl",
    position: "center",
    content: "각 설정 카테고리를 클릭해서 상세 옵션을 확인하세요.",
    details: "",
    highlight: true,
    isMainSection: false,
  },
  {
    id: 12,
    title: "모든 준비 완료! 🚀",
    page: "dashboard",
    target: null,
    position: "center",
    content: "축하합니다! 기가 버핏의 모든 핵심 기능을 둘러보셨습니다. 이제 AI와 함께 성공적인 투자 여정을 시작하세요!",
    details:
      "• 실제 투자 시작하기\n• 궁금한 점은 AI 채팅에서 질문\n• 정기적인 포트폴리오 점검\n• 투자 목표 달성을 위한 꾸준한 학습",
    highlight: false,
    isMainSection: true,
  },
]

interface LiveTutorialProps {
  onComplete: () => void
  onPageChange: (page: string) => void
  userProfile: any
  currentPage: string
}

export default function LiveTutorial({ onComplete, onPageChange, userProfile, currentPage }: LiveTutorialProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [highlightRect, setHighlightRect] = useState<DOMRect | null>(null)

  useEffect(() => {
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      document.body.style.overflow = originalOverflow
    }
  }, [])

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
        scrollToTargetAndHighlight()
      }, 600)
    } else {
      setTimeout(() => scrollToTargetAndHighlight(), 100)
    }
  }, [currentStep, onPageChange, currentPage])

  const scrollToTargetAndHighlight = () => {
    const step = tutorialSteps[currentStep]

    if (step.target && step.highlight) {
      const element = document.querySelector(step.target)
      if (element) {
        element.scrollIntoView({
          behavior: "smooth",
          block: "center",
          inline: "center",
        })

        setTimeout(() => {
          const rect = element.getBoundingClientRect()
          setHighlightRect(rect)
        }, 400)
      } else {
        setHighlightRect(null)
      }
    } else {
      setHighlightRect(null)
      if (step.page) {
        window.scrollTo({ top: 0, behavior: "smooth" })
      }
    }
  }

  const handleNext = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      setHighlightRect(null)
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

  const getTooltipPosition = () => {
    if (!highlightRect || currentTutorial.position === "center" || currentTutorial.isMainSection) {
      return "fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50"
    }
    return "fixed z-50"
  }

  const getTooltipStyle = () => {
    if (!highlightRect || currentTutorial.position === "center" || currentTutorial.isMainSection) {
      return {}
    }

    const tooltipWidth = currentTutorial.isMainSection ? 400 : 280
    const tooltipHeight = currentTutorial.isMainSection ? 300 : 150
    const safeMargin = 20
    const minDistance = 40

    const highlightLeft = highlightRect.left
    const highlightRight = highlightRect.right
    const highlightTop = highlightRect.top
    const highlightBottom = highlightRect.bottom

    const screenWidth = window.innerWidth
    const screenHeight = window.innerHeight

    let finalPosition = { top: 0, left: 0 }

    const spaceRight = screenWidth - highlightRight
    const spaceLeft = highlightLeft
    const spaceTop = highlightTop
    const spaceBottom = screenHeight - highlightBottom

    if (spaceLeft >= tooltipWidth + minDistance && spaceLeft >= Math.max(spaceRight, spaceTop, spaceBottom)) {
      finalPosition = {
        top: Math.max(safeMargin, Math.min(screenHeight - tooltipHeight - safeMargin, highlightTop)),
        left: Math.max(safeMargin, highlightLeft - tooltipWidth - minDistance),
      }
    } else if (spaceRight >= tooltipWidth + minDistance && spaceRight >= Math.max(spaceTop, spaceBottom)) {
      finalPosition = {
        top: Math.max(safeMargin, Math.min(screenHeight - tooltipHeight - safeMargin, highlightTop)),
        left: Math.min(screenWidth - tooltipWidth - safeMargin, highlightRight + minDistance),
      }
    } else if (spaceTop >= tooltipHeight + minDistance) {
      finalPosition = {
        top: Math.max(safeMargin, highlightTop - tooltipHeight - minDistance),
        left: Math.max(safeMargin, Math.min(screenWidth - tooltipWidth - safeMargin, highlightLeft)),
      }
    } else {
      finalPosition = {
        top: Math.min(screenHeight - tooltipHeight - safeMargin, highlightBottom + minDistance),
        left: Math.max(safeMargin, Math.min(screenWidth - tooltipWidth - safeMargin, highlightLeft)),
      }
    }

    return finalPosition
  }

  const getCardWidth = () => {
    return currentTutorial.isMainSection ? "w-[400px]" : "w-72"
  }

  return (
    <div className="fixed inset-0 z-50">
      {/* 배경 오버레이 */}
      <div className="absolute inset-0 bg-black/60 transition-all duration-300" />

      {/* 하이라이트 */}
      {highlightRect && currentTutorial.highlight && (
        <div
          className="absolute border-2 border-blue-400 rounded-lg transition-all duration-500 z-40 pointer-events-none"
          style={{
            top: highlightRect.top - 8,
            left: highlightRect.left - 8,
            width: highlightRect.width + 16,
            height: highlightRect.height + 16,
            boxShadow: "0 0 0 2px rgba(59, 130, 246, 0.3)",
          }}
        />
      )}

      {/* 튜토리얼 카드 */}
      <div className={`${getTooltipPosition()} ${getCardWidth()}`} style={getTooltipStyle()}>
        <Card className="shadow-xl border border-blue-400/50 bg-gray-900/95 backdrop-blur-sm transition-all duration-300">
          <CardContent className={currentTutorial.isMainSection ? "p-5" : "p-3"}>
            {/* 헤더 */}
            <div className="mb-3">
              <h3 className={`${currentTutorial.isMainSection ? "text-lg" : "text-sm"} font-bold text-white mb-2`}>
                {currentTutorial.title}
              </h3>
              <p className={`text-gray-300 ${currentTutorial.isMainSection ? "text-sm" : "text-xs"} leading-relaxed`}>
                {currentTutorial.content}
              </p>
            </div>

            {/* 상세 정보 - 메인 섹션만 */}
            {currentTutorial.isMainSection && currentTutorial.details && (
              <div className="mb-4">
                <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/30">
                  <h4 className="text-white font-medium mb-2 text-sm">주요 기능:</h4>
                  <div className="space-y-1">
                    {currentTutorial.details.split("\n").map((detail, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <div className="w-1 h-1 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-gray-300 text-xs leading-relaxed">{detail.replace("• ", "")}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 진행률 */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>
                  {currentStep + 1}/{tutorialSteps.length}
                </span>
                <span>{Math.round(progress)}% 완료</span>
              </div>
              <Progress value={progress} className="h-1.5 bg-gray-700" />
            </div>

            {/* 네비게이션 */}
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={handlePrev}
                disabled={currentStep === 0}
                size="sm"
                className="text-sm px-3 py-2 bg-transparent border-gray-600 text-gray-300 hover:bg-gray-700/50"
              >
                <ArrowLeftIcon className="w-4 h-4 mr-1" />
                이전
              </Button>

              <Button
                onClick={handleNext}
                disabled={isTransitioning}
                size="sm"
                className="text-sm px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white"
              >
                {currentStep === tutorialSteps.length - 1 ? "완료" : "다음"}
                {currentStep !== tutorialSteps.length - 1 && <ArrowRightIcon className="w-4 h-4 ml-1" />}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 페이지 표시 */}
      <div className="absolute top-4 left-4 z-40">
        <div className="bg-gray-900/80 backdrop-blur-sm rounded px-3 py-1.5 border border-gray-700/50">
          <p className="text-sm text-white font-medium">
            {currentTutorial.page === "dashboard"
              ? "📊 대시보드"
              : currentTutorial.page === "portfolio"
                ? "💼 포트폴리오"
                : currentTutorial.page === "ai-chat"
                  ? "🤖 AI 채팅"
                  : currentTutorial.page === "auto-trading"
                    ? "⚡ 자동매매"
                    : "⚙️ 설정"}
          </p>
        </div>
      </div>

      {/* 전환 안내 */}
      {isTransitioning && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-40">
          <div className="bg-blue-500/20 backdrop-blur-sm rounded-lg px-4 py-2 border border-blue-500/30 flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
            <p className="text-sm text-blue-300">섹션 이동 중...</p>
          </div>
        </div>
      )}
    </div>
  )
}
