"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  HomeIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  CogIcon,
  ArrowRightIcon,
  CheckIcon,
} from "@heroicons/react/24/outline"
import AnimatedCharacter from "../common/AnimatedCharacter"

const tutorialSections = [
  {
    id: 1,
    title: "대시보드",
    icon: HomeIcon,
    description: "투자 현황을 한눈에 확인하세요",
    features: [
      "📊 포트폴리오 총 가치 및 수익률 확인",
      "📈 실시간 차트로 성과 추적",
      "🚨 중요한 시장 알림 받기",
      "💰 보유 현금 및 투자 비중 관리",
    ],
    color: "from-blue-500 to-blue-600",
    bgColor: "bg-blue-50",
  },
  {
    id: 2,
    title: "포트폴리오",
    icon: ChartBarIcon,
    description: "스마트한 포트폴리오 관리",
    features: [
      "📋 보유 종목 상세 정보 확인",
      "⚖️ 포트폴리오 배분 최적화",
      "📊 개별 종목 수익률 분석",
      "🔄 자동 리밸런싱 기능",
    ],
    color: "from-green-500 to-green-600",
    bgColor: "bg-green-50",
  },
  {
    id: 3,
    title: "AI 채팅",
    icon: ChatBubbleLeftRightIcon,
    description: "AI 투자 전문가와 대화하세요",
    features: [
      "🤖 24/7 AI 투자 상담 서비스",
      "💡 개인 맞춤형 투자 조언",
      "📰 실시간 시장 분석 및 뉴스",
      "🎯 투자 전략 추천 및 검토",
    ],
    color: "from-purple-500 to-purple-600",
    bgColor: "bg-purple-50",
  },
  {
    id: 4,
    title: "설정",
    icon: CogIcon,
    description: "개인화된 투자 환경 설정",
    features: [
      "👤 프로필 및 투자 성향 관리",
      "🔔 알림 설정 및 맞춤화",
      "🔒 보안 설정 및 계정 관리",
      "🎨 테마 및 인터페이스 설정",
    ],
    color: "from-gray-500 to-gray-600",
    bgColor: "bg-gray-50",
  },
]

export default function SectionTutorial({
  onComplete,
  userProfile,
}: {
  onComplete: () => void
  userProfile: any
}) {
  const [currentSection, setCurrentSection] = useState(0)
  const progress = ((currentSection + 1) / tutorialSections.length) * 100

  const handleNext = () => {
    if (currentSection < tutorialSections.length - 1) {
      setCurrentSection(currentSection + 1)
    } else {
      onComplete()
    }
  }

  const handlePrev = () => {
    if (currentSection > 0) {
      setCurrentSection(currentSection - 1)
    }
  }

  const handleSkip = () => {
    onComplete()
  }

  const currentTutorial = tutorialSections[currentSection]
  const IconComponent = currentTutorial.icon

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* 헤더 */}
      <div className="flex justify-between items-center p-6">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-blue-600">기가 버핏</h1>
          <span className="text-gray-500">- 시작 가이드</span>
        </div>
        <Button variant="ghost" onClick={handleSkip} className="text-gray-500 hover:text-gray-700">
          건너뛰기
        </Button>
      </div>

      <div className="flex items-center justify-center px-4 py-8">
        <div className="max-w-4xl w-full">
          {/* 진행률 */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-600">
                {currentSection + 1} / {tutorialSections.length}
              </span>
              <span className="text-sm text-gray-500">{Math.round(progress)}% 완료</span>
            </div>
            <Progress value={progress} className="h-3" />
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* 왼쪽 - 캐릭터 */}
            <div className="text-center">
              <div className="mb-6">
                <AnimatedCharacter />
              </div>
              <div className="bg-white/80 backdrop-blur rounded-lg p-4 shadow-lg">
                <p className="text-lg font-medium text-gray-800 mb-2">
                  안녕하세요! {userProfile?.experience === "beginner" ? "투자 초보자" : "투자자"}님! 👋
                </p>
                <p className="text-gray-600">기가 버핏의 각 섹션을 소개해드릴게요. 함께 둘러보시죠!</p>
              </div>
            </div>

            {/* 오른쪽 - 섹션 소개 */}
            <div className="space-y-6">
              <Card className={`shadow-xl border-0 ${currentTutorial.bgColor}`}>
                <CardHeader className="text-center pb-4">
                  <div className="flex justify-center mb-4">
                    <div
                      className={`w-16 h-16 rounded-full bg-gradient-to-r ${currentTutorial.color} flex items-center justify-center shadow-lg`}
                    >
                      <IconComponent className="w-8 h-8 text-white" />
                    </div>
                  </div>
                  <CardTitle className="text-2xl font-bold text-gray-900">{currentTutorial.title}</CardTitle>
                  <p className="text-gray-600 text-lg">{currentTutorial.description}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <h4 className="font-semibold text-gray-800 mb-3">주요 기능:</h4>
                  <div className="space-y-3">
                    {currentTutorial.features.map((feature, index) => (
                      <div key={index} className="flex items-center space-x-3">
                        <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <CheckIcon className="w-4 h-4 text-green-600" />
                        </div>
                        <span className="text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>

                  {/* 개인화된 메시지 */}
                  {currentSection === 0 && userProfile?.riskTolerance === "conservative" && (
                    <div className="mt-4 p-3 bg-blue-100 rounded-lg">
                      <p className="text-sm text-blue-800">
                        💡 보수적인 투자 성향이시군요! 대시보드에서 안정적인 포트폴리오 성과를 확인하세요.
                      </p>
                    </div>
                  )}
                  {currentSection === 1 && userProfile?.investmentStyle === "longterm" && (
                    <div className="mt-4 p-3 bg-green-100 rounded-lg">
                      <p className="text-sm text-green-800">
                        💡 장기투자를 선호하시는군요! 포트폴리오에서 장기 성장 전략을 세워보세요.
                      </p>
                    </div>
                  )}
                  {currentSection === 2 && (
                    <div className="mt-4 p-3 bg-purple-100 rounded-lg">
                      <p className="text-sm text-purple-800">
                        💡 AI 채팅에서 "
                        {userProfile?.experience === "beginner" ? "초보자를 위한 투자 팁" : "고급 투자 전략"}"에 대해
                        물어보세요!
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 네비게이션 버튼 */}
              <div className="flex justify-between items-center">
                <Button
                  onClick={handlePrev}
                  disabled={currentSection === 0}
                  variant="outline"
                  className="px-6 py-3 bg-transparent"
                >
                  이전
                </Button>

                <div className="flex space-x-2">
                  {tutorialSections.map((_, index) => (
                    <div
                      key={index}
                      className={`w-3 h-3 rounded-full transition-colors ${
                        index === currentSection ? "bg-blue-500" : "bg-gray-300"
                      }`}
                    />
                  ))}
                </div>

                <Button
                  onClick={handleNext}
                  className={`px-6 py-3 bg-gradient-to-r ${currentTutorial.color} text-white hover:opacity-90`}
                >
                  {currentSection === tutorialSections.length - 1 ? (
                    "시작하기"
                  ) : (
                    <>
                      다음 <ArrowRightIcon className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
