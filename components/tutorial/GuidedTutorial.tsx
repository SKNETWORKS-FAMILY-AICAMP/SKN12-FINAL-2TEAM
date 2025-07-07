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
    description: "기가 버핏에 오신 것을 환영합니다! 각 섹션을 직접 둘러보며 기능을 알아보세요.",
    page: "dashboard",
    content: "먼저 대시보드에서 투자 현황을 확인하는 방법을 알아보겠습니다.",
    highlight: "전체 화면을 둘러보세요. 포트폴리오 요약, 성과 차트, 시장 알림을 한눈에 볼 수 있어요.",
  },
  {
    id: 2,
    title: "대시보드 📊",
    description: "현재 보고 계신 대시보드에서 투자 현황을 확인하세요.",
    page: "dashboard",
    content: "상단 카드들에서 총 자산, 수익률, 현금, 보유 종목 수를 확인할 수 있어요.",
    highlight: "차트를 통해 포트폴리오 성과와 자산 배분을 시각적으로 파악하세요.",
  },
  {
    id: 3,
    title: "포트폴리오 관리 📈",
    description: "이제 포트폴리오 섹션으로 이동해서 상세한 투자 관리 기능을 살펴보겠습니다.",
    page: "portfolio",
    content: "여기서 보유 종목의 상세 정보를 확인하고 포트폴리오를 관리할 수 있어요.",
    highlight: "개별 종목의 수익률, 매수/매도 기능, 포트폴리오 리밸런싱을 활용하세요.",
  },
  {
    id: 4,
    title: "AI 투자 상담 🤖",
    description: "AI 채팅 섹션에서 개인 맞춤형 투자 조언을 받아보세요.",
    page: "ai-chat",
    content: "24/7 AI 투자 전문가와 대화하며 투자 전략을 세울 수 있어요.",
    highlight: "투자 질문을 입력하거나 제안된 질문을 클릭해서 AI와 대화해보세요.",
  },
  {
    id: 5,
    title: "설정 및 개인화 ⚙️",
    description: "마지막으로 설정에서 개인 맞춤 환경을 구성해보세요.",
    page: "settings",
    content: "프로필, 알림 설정, 보안 등을 관리할 수 있어요.",
    highlight: "투자 성향과 알림 설정을 개인화하여 더 나은 투자 경험을 만들어보세요.",
  },
  {
    id: 6,
    title: "튜토리얼 완료! 🚀",
    description: "모든 기능을 둘러보셨습니다! 이제 기가 버핏을 자유롭게 사용해보세요.",
    page: "dashboard",
    content: "언제든지 AI 채팅에서 도움을 요청하거나 각 섹션을 자유롭게 탐색하세요.",
    highlight: "성공적인 투자를 위해 기가 버핏과 함께 시작해보세요!",
  },
]

interface GuidedTutorialProps {
  onComplete: () => void
  onPageChange: (page: string) => void
  userProfile: any
  currentPage: string
}

export default function GuidedTutorial({ onComplete, onPageChange, userProfile, currentPage }: GuidedTutorialProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)

  useEffect(() => {
    // 튜토리얼 시작 시 첫 번째 페이지로 이동
    if (currentStep === 0) {
      onPageChange("dashboard")
    }
  }, [])

  useEffect(() => {
    // 스텝이 변경될 때 해당 페이지로 이동
    const step = tutorialSteps[currentStep]
    if (step && step.page !== currentPage) {
      setIsTransitioning(true)
      onPageChange(step.page)

      // 페이지 전환 애니메이션을 위한 딜레이
      setTimeout(() => {
        setIsTransitioning(false)
      }, 300)
    }
  }, [currentStep, onPageChange])

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

  return (
    <div className="fixed inset-0 z-50">
      {/* 반투명 오버레이 */}
      <div className="absolute inset-0 bg-black bg-opacity-40" />

      {/* 튜토리얼 카드 */}
      <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 w-full max-w-2xl px-4">
        <Card className="shadow-2xl border-2 border-blue-400 bg-white">
          <CardContent className="p-6">
            {/* 헤더 */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-xl font-bold text-gray-900">{currentTutorial.title}</h3>
                  {isTransitioning && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  )}
                </div>
                <p className="text-gray-600 text-sm mb-3">{currentTutorial.description}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleSkip} className="text-gray-400 hover:text-gray-600 p-1">
                <XMarkIcon className="w-5 h-5" />
              </Button>
            </div>

            {/* 콘텐츠 */}
            <div className="mb-6">
              <div className="bg-blue-50 rounded-lg p-4 mb-4">
                <p className="text-blue-800 font-medium">{currentTutorial.content}</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700">{currentTutorial.highlight}</p>
              </div>

              {/* 개인화된 팁 */}
              {currentStep === 1 && userProfile?.experience === "beginner" && (
                <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-sm text-green-800">
                    💡 초보자 팁: 대시보드의 각 카드를 클릭해서 상세 정보를 확인해보세요!
                  </p>
                </div>
              )}

              {currentStep === 2 && userProfile?.investmentStyle === "longterm" && (
                <div className="mt-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                  <p className="text-sm text-purple-800">
                    💡 장기투자자 팁: 포트폴리오에서 자동 리밸런싱 기능을 활용해보세요!
                  </p>
                </div>
              )}

              {currentStep === 3 && userProfile?.riskTolerance === "conservative" && (
                <div className="mt-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <p className="text-sm text-orange-800">
                    💡 보수적 투자자 팁: AI에게 "안전한 투자 전략"에 대해 물어보세요!
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
                      index === currentStep ? "bg-blue-500" : "bg-gray-300"
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

      {/* 현재 페이지 표시 */}
      <div className="absolute top-6 left-6">
        <div className="bg-white/90 backdrop-blur rounded-lg px-4 py-2 border border-gray-200">
          <p className="text-sm font-medium text-gray-700">
            현재 위치:{" "}
            <span className="text-blue-600">
              {currentTutorial.page === "dashboard"
                ? "대시보드"
                : currentTutorial.page === "portfolio"
                  ? "포트폴리오"
                  : currentTutorial.page === "ai-chat"
                    ? "AI 채팅"
                    : "설정"}
            </span>
          </p>
        </div>
      </div>
    </div>
  )
}
