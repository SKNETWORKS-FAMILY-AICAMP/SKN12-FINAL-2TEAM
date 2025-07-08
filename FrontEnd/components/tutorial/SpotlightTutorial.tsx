"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { XMarkIcon, ArrowRightIcon, ArrowLeftIcon } from "@heroicons/react/24/outline"

const tutorialSteps = [
  {
    id: 1,
    title: "환영합니다! 🎉",
    description: "기가 버핏에 오신 것을 환영합니다! 각 섹션을 차례대로 소개해드릴게요.",
    target: null,
    position: "center",
    content: "AI와 함께하는 스마트한 투자 여정을 시작해보세요!",
  },
  {
    id: 2,
    title: "사이드바 네비게이션",
    description: "왼쪽 사이드바에서 다양한 섹션으로 이동할 수 있어요.",
    target: ".sidebar-nav",
    position: "right",
    content: "대시보드, 포트폴리오, AI 채팅, 설정 메뉴를 확인하세요.",
  },
  {
    id: 3,
    title: "대시보드 📊",
    description: "현재 보고 계신 대시보드에서 투자 현황을 한눈에 확인하세요.",
    target: ".dashboard-content",
    position: "center",
    content: "포트폴리오 총 가치, 수익률, 보유 현금 등을 실시간으로 확인할 수 있어요.",
  },
  {
    id: 4,
    title: "포트폴리오 요약 카드",
    description: "상단 카드들에서 핵심 투자 정보를 확인하세요.",
    target: ".portfolio-cards",
    position: "bottom",
    content: "총 자산, 수익률, 현금, 보유 종목 수를 빠르게 파악할 수 있어요.",
  },
  {
    id: 5,
    title: "성과 차트 📈",
    description: "포트폴리오 성과를 시각적으로 확인하세요.",
    target: ".performance-chart",
    position: "top",
    content: "시간별 포트폴리오 가치 변화와 자산 배분을 차트로 볼 수 있어요.",
  },
  {
    id: 6,
    title: "시장 알림 & 주요 종목",
    description: "중요한 시장 소식과 주요 종목 동향을 확인하세요.",
    target: ".market-section",
    position: "top",
    content: "실시간 시장 알림과 주요 종목의 가격 변동을 모니터링할 수 있어요.",
  },
  {
    id: 7,
    title: "알림 센터 🔔",
    description: "상단 우측의 알림 아이콘에서 중요한 소식을 확인하세요.",
    target: ".notification-bell",
    position: "bottom-left",
    content: "새로운 시장 소식이나 포트폴리오 변동 알림을 받을 수 있어요.",
  },
  {
    id: 8,
    title: "준비 완료! 🚀",
    description: "이제 기가 버핏의 모든 기능을 사용할 준비가 되었어요!",
    target: null,
    position: "center",
    content: "포트폴리오 섹션에서 상세한 투자 관리를, AI 채팅에서 투자 조언을 받아보세요!",
  },
]

interface SpotlightTutorialProps {
  onComplete: () => void
  userProfile: any
}

export default function SpotlightTutorial({ onComplete, userProfile }: SpotlightTutorialProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [spotlightStyle, setSpotlightStyle] = useState<any>({})

  useEffect(() => {
    updateSpotlight()
  }, [currentStep])

  const updateSpotlight = () => {
    const step = tutorialSteps[currentStep]
    if (!step.target) {
      setSpotlightStyle({})
      return
    }

    const element = document.querySelector(step.target)
    if (element) {
      const rect = element.getBoundingClientRect()
      const padding = 20

      setSpotlightStyle({
        top: rect.top - padding,
        left: rect.left - padding,
        width: rect.width + padding * 2,
        height: rect.height + padding * 2,
      })
    }
  }

  const handleNext = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    onComplete()
  }

  const currentTutorial = tutorialSteps[currentStep]
  const progress = ((currentStep + 1) / tutorialSteps.length) * 100

  const getTooltipPosition = () => {
    if (!currentTutorial.target) return "fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"

    const element = document.querySelector(currentTutorial.target)
    if (!element) return "fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"

    const rect = element.getBoundingClientRect()
    const tooltipWidth = 400
    const tooltipHeight = 200

    switch (currentTutorial.position) {
      case "right":
        return `fixed top-[${rect.top + rect.height / 2 - tooltipHeight / 2}px] left-[${rect.right + 20}px]`
      case "left":
        return `fixed top-[${rect.top + rect.height / 2 - tooltipHeight / 2}px] left-[${rect.left - tooltipWidth - 20}px]`
      case "top":
        return `fixed top-[${rect.top - tooltipHeight - 20}px] left-[${rect.left + rect.width / 2 - tooltipWidth / 2}px]`
      case "bottom":
        return `fixed top-[${rect.bottom + 20}px] left-[${rect.left + rect.width / 2 - tooltipWidth / 2}px]`
      case "bottom-left":
        return `fixed top-[${rect.bottom + 20}px] left-[${rect.left - tooltipWidth + rect.width}px]`
      default:
        return "fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
    }
  }

  return (
    <div className="fixed inset-0 z-50">
      {/* 오버레이 배경 */}
      <div className="absolute inset-0 bg-black bg-opacity-75 transition-all duration-500" />

      {/* 스포트라이트 효과 */}
      {currentTutorial.target && (
        <div
          className="absolute bg-transparent border-4 border-yellow-400 rounded-lg shadow-2xl transition-all duration-500 animate-pulse"
          style={{
            top: spotlightStyle.top,
            left: spotlightStyle.left,
            width: spotlightStyle.width,
            height: spotlightStyle.height,
            boxShadow: `0 0 0 9999px rgba(0, 0, 0, 0.75), 0 0 30px rgba(255, 255, 0, 0.5)`,
          }}
        />
      )}

      {/* 튜토리얼 툴팁 */}
      <div className={getTooltipPosition()}>
        <Card className="w-96 shadow-2xl border-2 border-yellow-400 bg-white">
          <CardContent className="p-6">
            {/* 헤더 */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">{currentTutorial.title}</h3>
                <p className="text-gray-600 text-sm mb-3">{currentTutorial.description}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleSkip} className="text-gray-400 hover:text-gray-600 p-1">
                <XMarkIcon className="w-5 h-5" />
              </Button>
            </div>

            {/* 콘텐츠 */}
            <div className="mb-6">
              <p className="text-gray-700">{currentTutorial.content}</p>

              {/* 개인화된 팁 */}
              {currentStep === 2 && userProfile?.experience === "beginner" && (
                <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800">
                    💡 초보자 팁: 대시보드에서 기본적인 투자 현황부터 천천히 익혀보세요!
                  </p>
                </div>
              )}

              {currentStep === 4 && userProfile?.riskTolerance === "conservative" && (
                <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-sm text-green-800">
                    💡 보수적 투자자 팁: 포트폴리오 카드에서 안정적인 수익률을 확인하세요!
                  </p>
                </div>
              )}
            </div>

            {/* 진행률 */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-500 mb-2">
                <span>
                  {currentStep + 1} / {tutorialSteps.length}
                </span>
                <span>{Math.round(progress)}% 완료</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            {/* 네비게이션 버튼 */}
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={handlePrev}
                disabled={currentStep === 0}
                className="flex items-center space-x-2 bg-transparent"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                <span>이전</span>
              </Button>

              <div className="flex space-x-1">
                {tutorialSteps.map((_, index) => (
                  <div
                    key={index}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      index === currentStep ? "bg-yellow-500" : "bg-gray-300"
                    }`}
                  />
                ))}
              </div>

              <Button
                onClick={handleNext}
                className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white flex items-center space-x-2"
              >
                <span>{currentStep === tutorialSteps.length - 1 ? "완료" : "다음"}</span>
                {currentStep !== tutorialSteps.length - 1 && <ArrowRightIcon className="w-4 h-4" />}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 건너뛰기 버튼 (우상단) */}
      <div className="absolute top-6 right-6">
        <Button
          variant="outline"
          onClick={handleSkip}
          className="bg-white/90 backdrop-blur border-gray-300 text-gray-700 hover:bg-white"
        >
          튜토리얼 건너뛰기
        </Button>
      </div>
    </div>
  )
}
