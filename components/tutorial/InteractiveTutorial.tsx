"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { XMarkIcon, ArrowRightIcon, ArrowLeftIcon, EyeIcon } from "@heroicons/react/24/outline"

const tutorialSteps = [
  {
    id: 1,
    title: "환영합니다! 🎉",
    description: "기가 버핏의 핵심 기능들을 실제 화면에서 직접 체험해보세요.",
    page: "dashboard",
    target: ".dashboard-content",
    position: "bottom-right",
    content: "대시보드에서 투자 현황을 실시간으로 확인할 수 있습니다. 각 카드를 클릭해보세요!",
    action: "카드를 클릭해서 상세 정보를 확인해보세요",
  },
  {
    id: 2,
    title: "포트폴리오 요약 📊",
    description: "투자 현황을 한눈에 파악하세요.",
    page: "dashboard",
    target: ".portfolio-cards",
    position: "bottom",
    content: "총 자산, 수익률, 현금, 보유 종목 수를 실시간으로 확인할 수 있습니다.",
    action: "각 카드에 마우스를 올려보고 클릭해보세요",
  },
  {
    id: 3,
    title: "성과 차트 분석 📈",
    description: "시각적으로 투자 성과를 분석하세요.",
    page: "dashboard",
    target: ".performance-chart",
    position: "top",
    content: "포트폴리오 성과와 자산 배분을 차트로 확인할 수 있습니다.",
    action: "차트 위에 마우스를 올려 상세 데이터를 확인해보세요",
  },
  {
    id: 4,
    title: "포트폴리오 관리 💼",
    description: "이제 포트폴리오 섹션으로 이동합니다.",
    page: "portfolio",
    target: null,
    position: "center",
    content: "여기서 보유 종목을 상세히 관리하고 새로운 투자를 할 수 있습니다.",
    action: "Add Position 버튼을 클릭해보세요",
  },
  {
    id: 5,
    title: "종목 관리 📋",
    description: "보유 종목의 상세 정보를 확인하세요.",
    page: "portfolio",
    target: ".tutorial-target-holdings-table",
    position: "top",
    content: "각 종목의 수익률과 상세 정보를 확인하고 거래할 수 있습니다.",
    action: "종목 행을 클릭하거나 '보기' 버튼을 클릭해보세요",
  },
  {
    id: 6,
    title: "AI 투자 상담 🤖",
    description: "AI와 투자 상담을 받아보세요.",
    page: "ai-chat",
    target: null,
    position: "center",
    content: "24/7 AI 투자 전문가와 대화하며 맞춤형 조언을 받을 수 있습니다.",
    action: "제안된 질문을 클릭하거나 직접 질문을 입력해보세요",
  },
  {
    id: 7,
    title: "설정 관리 ⚙️",
    description: "개인 맞춤 설정을 관리하세요.",
    page: "settings",
    target: ".max-w-4xl",
    position: "top",
    content: "투자 성향, 알림, 보안 등을 개인화할 수 있습니다.",
    action: "각 설정 카드를 클릭해서 상세 옵션을 확인해보세요",
  },
  {
    id: 8,
    title: "튜토리얼 완료! 🚀",
    description: "모든 기능을 체험해보셨습니다!",
    page: "dashboard",
    target: null,
    position: "center",
    content: "이제 기가 버핏의 모든 기능을 자유롭게 사용하실 수 있습니다.",
    action: "성공적인 투자를 위해 기가 버핏과 함께 시작하세요!",
  },
]

interface InteractiveTutorialProps {
  onComplete: () => void
  onPageChange: (page: string) => void
  userProfile: any
  currentPage: string
}

export default function InteractiveTutorial({
  onComplete,
  onPageChange,
  userProfile,
  currentPage,
}: InteractiveTutorialProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [highlightRect, setHighlightRect] = useState<DOMRect | null>(null)

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
        updateHighlight()
      }, 500)
    } else {
      setTimeout(() => updateHighlight(), 100)
    }
  }, [currentStep, onPageChange, currentPage])

  const updateHighlight = () => {
    const step = tutorialSteps[currentStep]
    if (step.target) {
      const element = document.querySelector(step.target)
      if (element) {
        const rect = element.getBoundingClientRect()
        setHighlightRect(rect)
      } else {
        setHighlightRect(null)
      }
    } else {
      setHighlightRect(null)
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

  const handleSkip = () => {
    setHighlightRect(null)
    onComplete()
  }

  const currentTutorial = tutorialSteps[currentStep]
  const progress = ((currentStep + 1) / tutorialSteps.length) * 100

  const getTooltipPosition = () => {
    if (!highlightRect) return "fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"

    const tooltipWidth = 400
    const tooltipHeight = 200

    switch (currentTutorial.position) {
      case "bottom":
        return `fixed top-[${highlightRect.bottom + 20}px] left-[${highlightRect.left + highlightRect.width / 2 - tooltipWidth / 2}px]`
      case "top":
        return `fixed top-[${highlightRect.top - tooltipHeight - 20}px] left-[${highlightRect.left + highlightRect.width / 2 - tooltipWidth / 2}px]`
      case "bottom-right":
        return `fixed top-[${highlightRect.bottom + 20}px] left-[${highlightRect.right - tooltipWidth}px]`
      default:
        return "fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
    }
  }

  return (
    <div className="fixed inset-0 z-50 animate-fade-in">
      {/* 오버레이 */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-all duration-500" />

      {/* 하이라이트 */}
      {highlightRect && (
        <div
          className="absolute bg-transparent border-4 border-blue-400 rounded-lg shadow-2xl transition-all duration-500"
          style={{
            top: highlightRect.top - 10,
            left: highlightRect.left - 10,
            width: highlightRect.width + 20,
            height: highlightRect.height + 20,
            boxShadow: `0 0 0 9999px rgba(0, 0, 0, 0.7), 0 0 30px rgba(59, 130, 246, 0.5)`,
            animation: "highlight-pulse 2s ease-in-out infinite",
          }}
        />
      )}

      {/* 튜토리얼 카드 */}
      <div className={getTooltipPosition()}>
        <Card className="w-96 shadow-2xl border-2 border-blue-400 bg-gray-800/95 backdrop-blur-sm animate-slide-up">
          <CardContent className="p-6">
            {/* 헤더 */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-xl font-bold text-white">{currentTutorial.title}</h3>
                  {isTransitioning && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  )}
                </div>
                <p className="text-gray-300 text-sm mb-3">{currentTutorial.description}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleSkip} className="text-gray-400 hover:text-white p-1">
                <XMarkIcon className="w-5 h-5" />
              </Button>
            </div>

            {/* 콘텐츠 */}
            <div className="mb-6">
              <div className="bg-blue-500/20 rounded-lg p-4 mb-4 border border-blue-500/30">
                <p className="text-blue-100 font-medium">{currentTutorial.content}</p>
              </div>

              <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/30">
                <div className="flex items-start space-x-3">
                  <EyeIcon className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">{currentTutorial.action}</p>
                </div>
              </div>
            </div>

            {/* 진행률 */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-400 mb-2">
                <span>
                  {currentStep + 1} / {tutorialSteps.length}
                </span>
                <span>{Math.round(progress)}% 완료</span>
              </div>
              <Progress value={progress} className="h-2 bg-gray-700" />
            </div>

            {/* 네비게이션 */}
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={handlePrev}
                disabled={currentStep === 0}
                className="flex items-center space-x-2 bg-transparent border-gray-600 text-gray-300 hover:bg-gray-700/50 hover:text-white"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                <span>이전</span>
              </Button>

              <div className="flex space-x-1">
                {tutorialSteps.map((_, index) => (
                  <div
                    key={index}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      index === currentStep ? "bg-blue-400" : "bg-gray-600"
                    }`}
                  />
                ))}
              </div>

              <Button
                onClick={handleNext}
                disabled={isTransitioning}
                className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white flex items-center space-x-2"
              >
                <span>{currentStep === tutorialSteps.length - 1 ? "완료" : "다음"}</span>
                {currentStep !== tutorialSteps.length - 1 && <ArrowRightIcon className="w-4 h-4" />}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 하이라이트 애니메이션 */}
      <style jsx>{`
        @keyframes highlight-pulse {
          0%, 100% {
            border-color: #3b82f6;
            box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7), 0 0 30px rgba(59, 130, 246, 0.5);
          }
          50% {
            border-color: #60a5fa;
            box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7), 0 0 40px rgba(59, 130, 246, 0.8);
          }
        }
      `}</style>
    </div>
  )
}
