"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { ArrowRightIcon, ArrowLeftIcon } from "@heroicons/react/24/outline"

const tutorialSteps = [
  {
    id: 1,
    title: "대시보드 - 투자 현황 한눈에 보기",
    image: "/images/tutorial/dashboard-screenshot.png",
    highlights: [
      {
        x: 50,
        y: 150,
        width: 800,
        height: 120,
        label: "포트폴리오 요약 카드",
        description: "총 자산, 수익률, 현금, 보유 종목 수를 한눈에 확인",
        position: "bottom",
      },
    ],
    explanation: {
      title: "📊 대시보드 둘러보기",
      content: [
        "💰 상단 카드에서 투자 현황을 빠르게 파악하세요",
        "📈 실시간으로 업데이트되는 포트폴리오 가치",
        "🚨 중요한 시장 변동 알림을 놓치지 마세요",
        "📊 차트로 투자 성과를 시각적으로 확인",
      ],
      tip: "각 카드를 클릭하면 상세 분석 화면으로 이동할 수 있어요!",
    },
  },
  {
    id: 2,
    title: "대시보드 - 성과 차트 분석",
    image: "/images/tutorial/dashboard-screenshot.png",
    highlights: [
      {
        x: 50,
        y: 300,
        width: 500,
        height: 250,
        label: "포트폴리오 성과 차트",
        description: "시간별 가치 변화 추이를 확인",
        position: "right",
      },
      {
        x: 580,
        y: 300,
        width: 300,
        height: 250,
        label: "자산 배분 차트",
        description: "종목별 투자 비중을 시각적으로 확인",
        position: "left",
      },
    ],
    explanation: {
      title: "📈 차트로 성과 분석하기",
      content: [
        "📊 포트폴리오 가치 변화 추이를 확인하세요",
        "🥧 자산 배분 차트로 투자 비중을 파악",
        "📅 기간별 수익률 비교 분석",
        "🔄 리밸런싱이 필요한 시점을 확인",
      ],
      tip: "차트 위에 마우스를 올리면 정확한 수치를 볼 수 있어요!",
    },
  },
  {
    id: 3,
    title: "대시보드 - 시장 정보 센터",
    image: "/images/tutorial/dashboard-screenshot.png",
    highlights: [
      {
        x: 50,
        y: 580,
        width: 400,
        height: 200,
        label: "시장 알림",
        description: "실시간 시장 소식과 중요 알림",
        position: "right",
      },
      {
        x: 480,
        y: 580,
        width: 400,
        height: 200,
        label: "주요 종목",
        description: "관심 종목의 실시간 가격 동향",
        position: "left",
      },
    ],
    explanation: {
      title: "🚨 시장 정보 확인하기",
      content: [
        "📰 중요한 시장 뉴스와 알림을 실시간으로 받아보세요",
        "⭐ 관심 종목의 가격 변동을 모니터링",
        "📊 주요 시장 지수 현황 확인",
        "🔔 개인 맞춤 알림 설정으로 놓치지 않기",
      ],
      tip: "알림을 클릭하면 관련 뉴스 전문을 볼 수 있어요!",
    },
  },
  {
    id: 4,
    title: "포트폴리오 - 보유 종목 관리",
    image: "/images/tutorial/portfolio-screenshot.png",
    highlights: [
      {
        x: 50,
        y: 200,
        width: 800,
        height: 300,
        label: "보유 종목 테이블",
        description: "개별 종목의 상세 정보와 수익률 확인",
        position: "bottom",
      },
    ],
    explanation: {
      title: "📋 포트폴리오 상세 관리",
      content: [
        "📈 각 종목의 실시간 가격과 수익률을 확인하세요",
        "💰 평균 매수가와 현재가를 비교 분석",
        "📊 종목별 투자 비중과 총 가치 파악",
        "💹 매수/매도 버튼으로 즉시 거래 가능",
      ],
      tip: "'View' 버튼을 클릭하면 종목 상세 분석을 볼 수 있어요!",
    },
  },
  {
    id: 5,
    title: "AI 채팅 - 투자 상담받기",
    image: "/images/tutorial/ai-chat-screenshot.png",
    highlights: [
      {
        x: 50,
        y: 100,
        width: 600,
        height: 400,
        label: "AI 채팅 대화창",
        description: "24/7 AI 투자 전문가와 실시간 상담",
        position: "right",
      },
    ],
    explanation: {
      title: "🤖 AI 투자 상담사 활용하기",
      content: [
        "💬 투자 관련 궁금한 점을 언제든 질문하세요",
        "📊 개인 맞춤형 투자 조언과 종목 분석",
        "💡 투자 전략 수립과 리스크 관리 조언",
        "📚 투자 용어와 개념을 쉽게 설명",
      ],
      tip: "구체적인 질문을 할수록 더 정확한 답변을 받을 수 있어요!",
    },
  },
  {
    id: 6,
    title: "AI 채팅 - 제안 질문 활용",
    image: "/images/tutorial/ai-chat-screenshot.png",
    highlights: [
      {
        x: 50,
        y: 520,
        width: 600,
        height: 80,
        label: "제안 질문 버튼들",
        description: "자주 묻는 질문들을 버튼으로 쉽게 선택",
        position: "top",
      },
    ],
    explanation: {
      title: "💡 스마트한 질문 방법",
      content: [
        "🎯 제안된 질문 버튼을 클릭해서 빠르게 시작",
        "📋 대화 요약 기능으로 핵심 내용 정리",
        "🔄 이전 대화 내용을 참고한 연속 질문",
        "📈 실시간 시장 데이터 기반 분석 요청",
      ],
      tip: "예시: '초보자를 위한 안전한 투자 방법'을 클릭해보세요!",
    },
  },
  {
    id: 7,
    title: "설정 - 개인화 설정",
    image: "/images/tutorial/settings-screenshot.png",
    highlights: [
      {
        x: 100,
        y: 150,
        width: 700,
        height: 400,
        label: "설정 카드들",
        description: "프로필, 알림, 보안, 화면 설정 관리",
        position: "bottom",
      },
    ],
    explanation: {
      title: "⚙️ 개인 맞춤 설정하기",
      content: [
        "👤 투자 성향과 위험 선호도를 설정하세요",
        "🔔 중요한 알림만 받도록 맞춤 설정",
        "🔒 2단계 인증으로 계정 보안 강화",
        "🎨 다크모드와 차트 색상 개인화",
      ],
      tip: "설정을 완료하면 더 정확한 맞춤형 서비스를 받을 수 있어요!",
    },
  },
  {
    id: 8,
    title: "튜토리얼 완료! 🎉",
    image: "/images/tutorial/dashboard-screenshot.png",
    highlights: [],
    explanation: {
      title: "🚀 기가 버핏과 함께 투자 시작!",
      content: [
        "✅ 모든 핵심 기능을 성공적으로 둘러보셨습니다",
        "💰 이제 실제 투자를 시작해보세요",
        "🤖 궁금한 점은 언제든 AI 채팅에서 질문",
        "📊 정기적인 포트폴리오 점검으로 성공 투자!",
      ],
      tip: "성공적인 투자 여정을 위해 기가 버핏이 함께하겠습니다!",
    },
  },
]

interface StaticImageTutorialProps {
  onComplete: () => void
  userProfile: any
}

export default function StaticImageTutorial({ onComplete, userProfile }: StaticImageTutorialProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  const handleNext = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1)
      setImageLoaded(false)
      setImageError(false)
    } else {
      onComplete()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
      setImageLoaded(false)
      setImageError(false)
    }
  }

  const handleSkip = () => {
    onComplete()
  }

  const currentTutorial = tutorialSteps[currentStep]
  const progress = ((currentStep + 1) / tutorialSteps.length) * 100

  return (
    <div className="fixed inset-0 z-50 bg-gradient-to-br from-navy-900 via-navy-800 to-slate-900">
      {/* 헤더 */}
      <div className="flex justify-between items-center p-4 border-b border-navy-700/50 bg-navy-800/50 backdrop-blur-sm">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
            기가 버핏
          </h1>
          <span className="text-gray-300">- 사용법 가이드</span>
        </div>
        <Button
          variant="ghost"
          onClick={handleSkip}
          className="text-gray-300 hover:text-white hover:bg-navy-700/50 transition-all duration-300"
        >
          튜토리얼 건너뛰기
        </Button>
      </div>

      {/* 진행률 */}
      <div className="px-4 py-2 bg-navy-800/30 backdrop-blur-sm border-b border-navy-700/50">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-300">
            {currentStep + 1} / {tutorialSteps.length} - {currentTutorial.title}
          </span>
          <span className="text-sm text-gray-400">{Math.round(progress)}% 완료</span>
        </div>
        <Progress value={progress} className="h-2 bg-navy-700" />
      </div>

      {/* 메인 콘텐츠 */}
      <div className="flex h-[calc(100vh-120px)]">
        {/* 이미지 영역 */}
        <div className="flex-1 relative bg-navy-800/30 overflow-hidden">
          {/* 로딩 상태 또는 에러 상태 */}
          {(!imageLoaded || imageError) && (
            <div className="absolute inset-0 flex items-center justify-center bg-navy-800/50 backdrop-blur-sm">
              <div className="text-center">
                {imageError ? (
                  <>
                    <div className="w-16 h-16 bg-navy-700 rounded-lg mx-auto mb-4 flex items-center justify-center">
                      <span className="text-2xl">🖼️</span>
                    </div>
                    <p className="text-gray-300 mb-2">화면 이미지를 준비 중입니다</p>
                    <p className="text-sm text-gray-400">곧 실제 화면으로 업데이트됩니다</p>
                  </>
                ) : (
                  <>
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
                    <p className="text-gray-300">화면을 불러오는 중...</p>
                  </>
                )}
              </div>
            </div>
          )}

          <img
            src={currentTutorial.image || "/placeholder.svg"}
            alt={currentTutorial.title}
            className={`w-full h-full object-contain transition-opacity duration-300 ${
              imageLoaded && !imageError ? "opacity-100" : "opacity-0"
            }`}
            onLoad={() => {
              setImageLoaded(true)
              setImageError(false)
            }}
            onError={() => {
              console.warn("Image not found, using placeholder:", currentTutorial.image)
              setImageError(true)
              setImageLoaded(true)
            }}
          />

          {/* 하이라이트 오버레이 - 이미지 로드 성공 시에만 표시 */}
          {imageLoaded &&
            !imageError &&
            currentTutorial.highlights.map((highlight, index) => (
              <div key={index}>
                {/* 하이라이트 박스 */}
                <div
                  className="absolute border-4 border-green-400 bg-green-400 bg-opacity-10 rounded-lg"
                  style={{
                    left: `${highlight.x}px`,
                    top: `${highlight.y}px`,
                    width: `${highlight.width}px`,
                    height: `${highlight.height}px`,
                    animation: "highlight-pulse 2s ease-in-out infinite",
                  }}
                />

                {/* 라벨과 화살표 */}
                <div
                  className="absolute z-10"
                  style={{
                    left:
                      highlight.position === "right"
                        ? `${highlight.x + highlight.width + 20}px`
                        : highlight.position === "left"
                          ? `${highlight.x - 220}px`
                          : `${highlight.x + highlight.width / 2 - 100}px`,
                    top:
                      highlight.position === "top"
                        ? `${highlight.y - 100}px`
                        : highlight.position === "bottom"
                          ? `${highlight.y + highlight.height + 20}px`
                          : `${highlight.y + highlight.height / 2 - 50}px`,
                  }}
                >
                  <div className="bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg max-w-xs">
                    <div className="font-bold text-sm mb-1">{highlight.label}</div>
                    <div className="text-xs">{highlight.description}</div>
                  </div>

                  {/* 화살표 */}
                  <div
                    className={`absolute w-0 h-0 ${
                      highlight.position === "right"
                        ? "border-t-8 border-b-8 border-r-8 border-t-transparent border-b-transparent border-r-green-500 -left-2 top-1/2 transform -translate-y-1/2"
                        : highlight.position === "left"
                          ? "border-t-8 border-b-8 border-l-8 border-t-transparent border-b-transparent border-l-green-500 -right-2 top-1/2 transform -translate-y-1/2"
                          : highlight.position === "top"
                            ? "border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-green-500 -bottom-2 left-1/2 transform -translate-x-1/2"
                            : "border-l-8 border-r-8 border-b-8 border-l-transparent border-r-transparent border-b-green-500 -top-2 left-1/2 transform -translate-x-1/2"
                    }`}
                  />
                </div>
              </div>
            ))}

          {/* 이미지 에러 시 가상 하이라이트 표시 */}
          {imageError &&
            currentTutorial.highlights.map((highlight, index) => (
              <div key={index}>
                <div
                  className="absolute border-4 border-blue-400 bg-blue-400 bg-opacity-10 rounded-lg"
                  style={{
                    left: "20%",
                    top: `${20 + index * 15}%`,
                    width: "60%",
                    height: "15%",
                    animation: "highlight-pulse 2s ease-in-out infinite",
                  }}
                />
                <div
                  className="absolute z-10 bg-blue-500 text-white px-3 py-2 rounded-lg shadow-lg"
                  style={{
                    left: "85%",
                    top: `${22 + index * 15}%`,
                  }}
                >
                  <div className="font-bold text-sm">{highlight.label}</div>
                  <div className="text-xs">{highlight.description}</div>
                </div>
              </div>
            ))}
        </div>

        {/* 설명 패널 */}
        <div className="w-96 bg-navy-800/50 backdrop-blur-sm border-l border-navy-700/50 flex flex-col">
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-3">{currentTutorial.explanation.title}</h2>

              <div className="space-y-3 mb-6">
                {currentTutorial.explanation.content.map((item, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-gray-300 leading-relaxed">{item}</p>
                  </div>
                ))}
              </div>

              {/* 팁 */}
              <div className="bg-gradient-to-r from-blue-500/20 to-green-500/20 rounded-lg p-4 border border-blue-500/30">
                <div className="flex items-start space-x-3">
                  <span className="text-2xl">💡</span>
                  <div>
                    <div className="font-semibold text-blue-300 mb-1">꿀팁!</div>
                    <p className="text-gray-300 text-sm">{currentTutorial.explanation.tip}</p>
                  </div>
                </div>
              </div>

              {/* 개인화된 팁 */}
              {currentStep === 0 && userProfile?.experience === "beginner" && (
                <div className="mt-4 p-4 bg-green-500/20 rounded-lg border border-green-500/30">
                  <p className="text-sm text-green-300">
                    🌱 <strong>초보자 특별 팁:</strong> 처음에는 대시보드의 총 자산 카드부터 천천히 확인해보세요!
                  </p>
                </div>
              )}

              {currentStep === 3 && userProfile?.investmentStyle === "longterm" && (
                <div className="mt-4 p-4 bg-purple-500/20 rounded-lg border border-purple-500/30">
                  <p className="text-sm text-purple-300">
                    📈 <strong>장기투자자 팁:</strong> 포트폴리오 테이블에서 각 종목의 장기 성과를 정기적으로
                    점검하세요!
                  </p>
                </div>
              )}

              {currentStep === 4 && userProfile?.riskTolerance === "conservative" && (
                <div className="mt-4 p-4 bg-orange-500/20 rounded-lg border border-orange-500/30">
                  <p className="text-sm text-orange-300">
                    🛡️ <strong>보수적 투자자 팁:</strong> AI 채팅에서 "안전한 배당주 추천"을 요청해보세요!
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* 네비게이션 버튼 */}
          <div className="p-6 border-t border-navy-700/50 bg-navy-800/30 backdrop-blur-sm">
            <div className="flex justify-between items-center mb-4">
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
            </div>

            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={handlePrev}
                disabled={currentStep === 0}
                className="flex items-center space-x-2 bg-transparent border-navy-600 text-gray-300 hover:bg-navy-700/50 hover:text-white hover:border-navy-500 transition-all duration-300"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                <span>이전</span>
              </Button>

              <Button
                onClick={handleNext}
                className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white flex items-center space-x-2 transition-all duration-300 hover:shadow-lg"
              >
                <span>{currentStep === tutorialSteps.length - 1 ? "완료하기" : "다음"}</span>
                {currentStep !== tutorialSteps.length - 1 && <ArrowRightIcon className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 하이라이트 애니메이션 CSS */}
      <style jsx>{`
        @keyframes highlight-pulse {
          0%,
          100% {
            border-color: #4ade80;
            background-color: rgba(74, 222, 128, 0.1);
            transform: scale(1);
          }
          50% {
            border-color: #22c55e;
            background-color: rgba(74, 222, 128, 0.2);
            transform: scale(1.02);
          }
        }
      `}</style>
    </div>
  )
}
