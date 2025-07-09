"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChevronDownIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  BoltIcon,
  AcademicCapIcon,
} from "@heroicons/react/24/outline"
import { useRouter } from "next/navigation"

const features = [
  {
    id: 1,
    title: "AI 투자 상담",
    description: "24/7 개인 맞춤형 투자 조언",
    details: [
      "실시간 시장 분석과 종목 추천",
      "개인 투자 성향에 맞는 맞춤형 전략",
      "리스크 관리와 포트폴리오 최적화",
      "투자 교육과 용어 설명",
    ],
    icon: ChatBubbleLeftRightIcon,
    gradient: "from-blue-500 to-purple-600",
  },
  {
    id: 2,
    title: "스마트 포트폴리오",
    description: "자동화된 포트폴리오 관리",
    details: [
      "실시간 포트폴리오 가치 추적",
      "자동 리밸런싱과 분산투자",
      "성과 분석과 벤치마크 비교",
      "세금 최적화 전략",
    ],
    icon: ChartBarIcon,
    gradient: "from-green-500 to-blue-600",
  },
  {
    id: 3,
    title: "자동매매 시스템",
    description: "AI 기반 자동 거래 실행",
    details: [
      "개인 맞춤형 매매 전략 수립",
      "감정 배제한 체계적 거래",
      "실시간 시장 모니터링",
      "거래 내역과 근거 상세 분석",
    ],
    icon: BoltIcon,
    gradient: "from-yellow-500 to-red-600",
  },
  {
    id: 4,
    title: "투자 교육",
    description: "게임화된 투자 학습",
    details: [
      "단계별 투자 지식 습득",
      "실전 시뮬레이션 연습",
      "투자 심리학과 행동 경제학",
      "성공 투자자들의 철학 학습",
    ],
    icon: AcademicCapIcon,
    gradient: "from-purple-500 to-pink-600",
  },
]

export default function WelcomePage({ onGetStarted }: { onGetStarted: () => void }) {
  const [currentSection, setCurrentSection] = useState(0)
  const [isScrolling, setIsScrolling] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const lastWheelTime = useRef(0)
  const [widths, setWidths] = useState<string[][]>(features.map(() => Array(4).fill("100%")))
  const router = useRouter()

  // 총 섹션 수 (히어로 + 기능들 + CTA)
  const totalSections = features.length + 2

  // 섹션으로 스크롤하는 함수
  const scrollToSection = (sectionIndex: number) => {
    if (isScrolling) return

    setIsScrolling(true)
    setCurrentSection(sectionIndex)

    const section = document.querySelector(`#section-${sectionIndex}`)
    if (section) {
      section.scrollIntoView({
        behavior: "smooth",
        block: "start",
      })
    }

    // 스크롤 완료 후 플래그 해제 (더 짧게)
    setTimeout(() => {
      setIsScrolling(false)
    }, 600)
  }

  // 휠 이벤트로 다음/이전 섹션 이동 (디바운싱 추가)
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault()

      const now = Date.now()

      // 디바운싱: 마지막 휠 이벤트로부터 300ms 이내면 무시
      if (now - lastWheelTime.current < 300) {
        return
      }

      // 스크롤 중이면 무시
      if (isScrolling) {
        return
      }

      // 휠 강도 체크 (너무 작은 움직임은 무시)
      if (Math.abs(e.deltaY) < 10) {
        return
      }

      lastWheelTime.current = now

      // 스크롤 방향 감지
      if (e.deltaY > 0) {
        // 아래로 스크롤 - 다음 섹션
        const nextSection = Math.min(totalSections - 1, currentSection + 1)
        if (nextSection !== currentSection) {
          scrollToSection(nextSection)
        }
      } else {
        // 위로 스크롤 - 이전 섹션
        const prevSection = Math.max(0, currentSection - 1)
        if (prevSection !== currentSection) {
          scrollToSection(prevSection)
        }
      }
    }

    const container = containerRef.current
    if (container) {
      container.addEventListener("wheel", handleWheel, { passive: false })
      return () => container.removeEventListener("wheel", handleWheel)
    }
  }, [currentSection, isScrolling, totalSections])

  // 터치 이벤트 (모바일) - 디바운싱 추가
  useEffect(() => {
    let startY = 0
    let lastTouchTime = 0

    const handleTouchStart = (e: TouchEvent) => {
      startY = e.touches[0].clientY
    }

    const handleTouchEnd = (e: TouchEvent) => {
      const now = Date.now()

      // 디바운싱: 마지막 터치로부터 400ms 이내면 무시
      if (now - lastTouchTime < 400) {
        return
      }

      if (isScrolling) return

      const endY = e.changedTouches[0].clientY
      const deltaY = startY - endY

      // 터치 민감도 (더 크게 설정)
      if (Math.abs(deltaY) > 80) {
        lastTouchTime = now

        if (deltaY > 0) {
          // 위로 스와이프 - 다음 섹션
          const nextSection = Math.min(totalSections - 1, currentSection + 1)
          if (nextSection !== currentSection) {
            scrollToSection(nextSection)
          }
        } else {
          // 아래로 스와이프 - 이전 섹션
          const prevSection = Math.max(0, currentSection - 1)
          if (prevSection !== currentSection) {
            scrollToSection(prevSection)
          }
        }
      }
    }

    const container = containerRef.current
    if (container) {
      container.addEventListener("touchstart", handleTouchStart, { passive: true })
      container.addEventListener("touchend", handleTouchEnd, { passive: true })
      return () => {
        container.removeEventListener("touchstart", handleTouchStart)
        container.removeEventListener("touchend", handleTouchEnd)
      }
    }
  }, [currentSection, isScrolling, totalSections])

  // 키보드 네비게이션 - 디바운싱 추가
  useEffect(() => {
    let lastKeyTime = 0

    const handleKeyDown = (e: KeyboardEvent) => {
      const now = Date.now()

      // 디바운싱: 마지막 키 입력으로부터 200ms 이내면 무시
      if (now - lastKeyTime < 200) {
        return
      }

      if (isScrolling) return

      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault()
        lastKeyTime = now
        const nextSection = Math.min(totalSections - 1, currentSection + 1)
        if (nextSection !== currentSection) {
          scrollToSection(nextSection)
        }
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault()
        lastKeyTime = now
        const prevSection = Math.max(0, currentSection - 1)
        if (prevSection !== currentSection) {
          scrollToSection(prevSection)
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [currentSection, isScrolling, totalSections])

  useEffect(() => {
    // 클라이언트에서만 랜덤 width 생성
    setWidths(
      features.map(() =>
        Array(4)
          .fill(0)
          .map(() => `${Math.random() * 60 + 40}%`)
      )
    )
  }, [])

  return (
    <div
      ref={containerRef}
      className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-slate-900 overflow-x-hidden"
      style={{ height: "100vh", overflow: "hidden" }}
    >
      {/* 상단 네비게이션 바 */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center p-6 backdrop-blur-md bg-black/50 border-b border-gray-800/50 transition-all duration-500 ease-out">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
          기가 버핏
        </h1>
        <div className="flex gap-4">
          <Button
            variant="ghost"
            className="text-gray-300 hover:text-white hover:bg-gray-800/50 transition-all duration-300 ease-out"
            onClick={() => router.push("/login")}
          >
            로그인
          </Button>
          <Button
            variant="outline"
            className="border-gray-700 text-gray-300 hover:bg-gray-800/50 hover:text-white hover:border-gray-600 bg-transparent transition-all duration-300 ease-out"
            onClick={() => router.push("/accountCreation")}
          >
            회원가입
          </Button>
        </div>
      </nav>

      {/* 히어로 섹션 */}
      <section id="section-0" className="min-h-screen flex items-center justify-center px-4 pt-20">
        <div className="max-w-7xl w-full grid md:grid-cols-2 gap-16 items-center">
          {/* 왼쪽 - 황소 캐릭터 */}
          <div className="text-center md:text-left order-2 md:order-1 animate-slide-up">
            <div className="mb-8 flex justify-center md:justify-start relative">
              {/* 황소 캐릭터 컨테이너 */}
              <div className="relative w-[500px] h-[500px] flex items-center justify-center">
                {/* 차트 배경만 - 단순하게 */}
                <div className="absolute inset-0 rounded-full overflow-hidden z-5">
                  <div className="absolute inset-0 opacity-30">
                    <img
                      src="/images/chart-background.png"
                      alt="주식 차트 배경"
                      className="w-full h-full object-cover scale-[2.0] transition-all duration-700 ease-out"
                    />
                  </div>
                </div>

                {/* 황소 이미지 - 선명하게 앞에 */}
                <div className="relative z-20 animate-float">
                  <img
                    src="/images/bull-character.png"
                    alt="기가 버핏 황소 캐릭터"
                    className="w-[420px] h-[420px] object-contain drop-shadow-2xl transition-all duration-700 ease-out"
                  />
                </div>

                {/* 전문적인 인디케이터들 */}
                <div className="absolute top-16 right-20 w-3 h-3 bg-green-400 rounded-full animate-pulse z-25 transition-all duration-500 ease-out"></div>
                <div
                  className="absolute bottom-16 left-20 w-2 h-2 bg-blue-400 rounded-full animate-pulse z-25 transition-all duration-500 ease-out"
                  style={{ animationDelay: "1s" }}
                ></div>
                <div
                  className="absolute top-24 left-16 w-2 h-2 bg-cyan-400 rounded-full animate-pulse z-25 transition-all duration-500 ease-out"
                  style={{ animationDelay: "1.5s" }}
                ></div>
                <div
                  className="absolute bottom-24 right-16 w-3 h-3 bg-emerald-400 rounded-full animate-pulse z-25 transition-all duration-500 ease-out"
                  style={{ animationDelay: "2s" }}
                ></div>
              </div>
            </div>
          </div>

          {/* 오른쪽 - 텍스트와 기능 소개 */}
          <div className="space-y-8 order-1 md:order-2 animate-slide-up" style={{ animationDelay: "0.2s" }}>
            <div>
              <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight transition-all duration-700 ease-out">
                투자의 새로운
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">혁명</span>
              </h1>
              <p className="text-xl text-gray-300 mb-8 leading-relaxed transition-all duration-700 ease-out">
                AI와 함께하는 스마트한 투자 여정을 시작하세요.
                <br />
                개인 맞춤형 포트폴리오 관리부터 자동매매까지
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  onClick={onGetStarted}
                  className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white px-10 py-4 text-xl font-semibold rounded-xl shadow-lg transform transition-all duration-500 ease-out hover:scale-105 hover:shadow-xl"
                >
                  무료로 시작하기
                </Button>
                <Button
                  variant="outline"
                  onClick={() => scrollToSection(1)}
                  className="border-2 border-gray-700 text-gray-300 hover:bg-gray-800/50 hover:text-white hover:border-gray-600 px-10 py-4 text-xl font-semibold rounded-xl bg-transparent transition-all duration-500 ease-out"
                >
                  더 알아보기
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* 스크롤 다운 인디케이터 */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <button
            onClick={() => scrollToSection(1)}
            className="flex flex-col items-center text-gray-400 hover:text-white transition-all duration-500 ease-out"
          >
            <span className="text-sm mb-2">스크롤하여 더 보기</span>
            <ChevronDownIcon className="w-6 h-6" />
          </button>
        </div>
      </section>

      {/* 기능 소개 섹션들 */}
      {features.map((feature, index) => {
        const IconComponent = feature.icon
        return (
          <section
            key={feature.id}
            id={`section-${index + 1}`}
            className="min-h-screen flex items-center justify-center px-4 py-20"
          >
            <div className="max-w-6xl w-full">
              <div
                className={`grid md:grid-cols-2 gap-12 items-center transition-all duration-700 ease-out ${index % 2 === 1 ? "md:grid-flow-col-dense" : ""}`}
              >
                {/* 텍스트 콘텐츠 */}
                <div className={`space-y-6 ${index % 2 === 1 ? "md:col-start-2" : ""}`}>
                  <div className="flex items-center space-x-4 mb-6">
                    <div
                      className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center shadow-xl transition-all duration-500 ease-out hover:scale-110`}
                    >
                      <IconComponent className="w-8 h-8 text-white" />
                    </div>
                    <div>
                      <h2 className="text-4xl font-bold text-white mb-2 transition-all duration-500 ease-out">
                        {feature.title}
                      </h2>
                      <p className="text-xl text-gray-300 transition-all duration-500 ease-out">
                        {feature.description}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {feature.details.map((detail, detailIndex) => (
                      <div
                        key={detailIndex}
                        className="flex items-start space-x-3 transition-all duration-500 ease-out"
                        style={{ transitionDelay: `${detailIndex * 100}ms` }}
                      >
                        <div className="w-2 h-2 bg-gradient-to-r from-green-400 to-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-gray-300 text-lg leading-relaxed">{detail}</p>
                      </div>
                    ))}
                  </div>

                  <Button
                    onClick={onGetStarted}
                    className={`bg-gradient-to-r ${feature.gradient} hover:opacity-90 text-white px-8 py-3 text-lg font-semibold rounded-xl shadow-lg transform transition-all duration-500 ease-out hover:scale-105`}
                  >
                    지금 시작하기
                  </Button>
                </div>

                {/* 시각적 요소 */}
                <div className={`${index % 2 === 1 ? "md:col-start-1" : ""}`}>
                  <Card className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 shadow-2xl hover:shadow-3xl transition-all duration-700 ease-out transform hover:scale-105">
                    <CardContent className="p-8">
                      <div className="space-y-6">
                        <div
                          className={`w-full h-4 bg-gradient-to-r ${feature.gradient} rounded-full opacity-20 transition-all duration-700 ease-out`}
                        ></div>
                        <div className="space-y-4">
                          {[...Array(4)].map((_, i) => (
                            <div
                              key={i}
                              className="flex items-center space-x-4 transition-all duration-500 ease-out"
                              style={{ transitionDelay: `${i * 150}ms` }}
                            >
                              <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${feature.gradient}`}></div>
                              <div className="flex-1 h-2 bg-gray-700 rounded-full">
                                <div
                                  className={`h-full bg-gradient-to-r ${feature.gradient} rounded-full transition-all duration-1000 ease-out`}
                                  style={{ width: widths[index][i] }}
                                ></div>
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="text-center">
                          <IconComponent className="w-16 h-16 text-gray-600 mx-auto transition-all duration-500 ease-out hover:text-gray-400" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </section>
        )
      })}

      {/* CTA 섹션 */}
      <section
        id={`section-${totalSections - 1}`}
        className="min-h-screen flex items-center justify-center px-4 py-20 bg-gradient-to-t from-black to-gray-900"
      >
        <div className="max-w-4xl w-full text-center space-y-8">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-6 transition-all duration-700 ease-out">
            지금 바로
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">
              시작하세요
            </span>
          </h2>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto transition-all duration-700 ease-out">
            수백만 명의 투자자들이 이미 기가 버핏과 함께 성공적인 투자를 하고 있습니다. 당신도 지금 시작해보세요.
          </p>

          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {[
              { number: "1M+", label: "활성 사용자" },
              { number: "₩500B+", label: "관리 자산" },
              { number: "98%", label: "고객 만족도" },
            ].map((stat, index) => (
              <Card
                key={index}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 shadow-xl transition-all duration-500 ease-out hover:scale-105"
                style={{ transitionDelay: `${index * 200}ms` }}
              >
                <CardContent className="p-6 text-center">
                  <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400 mb-2">
                    {stat.number}
                  </div>
                  <div className="text-gray-300">{stat.label}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Button
            onClick={onGetStarted}
            className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white px-12 py-6 text-2xl font-bold rounded-2xl shadow-2xl transform transition-all duration-500 ease-out hover:scale-110 hover:shadow-3xl"
          >
            무료로 시작하기
          </Button>
        </div>
      </section>

      {/* 하단 푸터 */}
      <footer className="text-center py-8 text-gray-400 border-t border-gray-800/50 bg-black/50 backdrop-blur-sm transition-all duration-500 ease-out">
        <p>&copy; 2024 기가 버핏. 모든 권리 보유.</p>
      </footer>

      {/* 애니메이션 CSS */}
      <style jsx>{`
      @keyframes float {
        0%, 100% {
          transform: translateY(0px) rotate(0deg);
        }
        25% {
          transform: translateY(-20px) rotate(1deg);
        }
        50% {
          transform: translateY(-40px) rotate(0deg);
        }
        75% {
          transform: translateY(-20px) rotate(-1deg);
        }
      }
      
      .animate-float {
        animation: float 10s ease-in-out infinite;
      }

      /* 스크롤바 숨기기 */
      ::-webkit-scrollbar {
        display: none;
      }
      
      html {
        -ms-overflow-style: none;
        scrollbar-width: none;
      }

      /* 부드러운 전환 효과 */
      * {
        transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
      }
    `}</style>
    </div>
  )
}
