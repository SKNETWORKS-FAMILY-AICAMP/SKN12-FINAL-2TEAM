"use client"

import { useState, useEffect } from "react"

const clickMessages = [
  "안녕하세요! 투자를 시작해볼까요? 💰",
  "오늘도 좋은 투자 기회를 찾아보세요! 📈",
  "저와 함께 부자가 되어봐요! 🤑",
  "투자는 장기적인 관점이 중요해요! 🎯",
  "분산투자를 잊지 마세요! 🌟",
  "리스크 관리가 성공의 열쇠예요! 🔑",
  "꾸준함이 최고의 투자 전략이에요! 💪",
  "오늘 하루도 화이팅! 🚀",
]

const specialAnimations = ["animate-bounce", "animate-pulse", "animate-spin", "animate-wiggle", "animate-ping"]

export default function AnimatedCharacter() {
  const [isWaving, setIsWaving] = useState(false)
  const [currentCharacter, setCurrentCharacter] = useState(1)
  const [isFloating, setIsFloating] = useState(true)
  const [clickMessage, setClickMessage] = useState("")
  const [showClickMessage, setShowClickMessage] = useState(false)
  const [clickAnimation, setClickAnimation] = useState("")
  const [clickCount, setClickCount] = useState(0)
  const [isExcited, setIsExcited] = useState(false)

  useEffect(() => {
    // 주기적으로 캐릭터 변경 (표정 변화)
    const characterInterval = setInterval(() => {
      if (!isExcited) {
        setCurrentCharacter((prev) => (prev === 1 ? 2 : 1))
      }
    }, 3000)

    // 주기적으로 손 흔들기 애니메이션
    const waveInterval = setInterval(() => {
      if (!showClickMessage) {
        setIsWaving(true)
        setTimeout(() => setIsWaving(false), 2000)
      }
    }, 8000)

    // 떠다니는 애니메이션 토글
    const floatInterval = setInterval(() => {
      setIsFloating((prev) => !prev)
    }, 4000)

    return () => {
      clearInterval(characterInterval)
      clearInterval(waveInterval)
      clearInterval(floatInterval)
    }
  }, [showClickMessage, isExcited])

  const handleCharacterClick = () => {
    // 클릭 카운트 증가
    setClickCount((prev) => prev + 1)

    // 랜덤 메시지 선택
    const randomMessage = clickMessages[Math.floor(Math.random() * clickMessages.length)]
    setClickMessage(randomMessage)

    // 랜덤 애니메이션 선택
    const randomAnimation = specialAnimations[Math.floor(Math.random() * specialAnimations.length)]
    setClickAnimation(randomAnimation)

    // 메시지 표시
    setShowClickMessage(true)

    // 캐릭터 변경 (흥분한 상태)
    setIsExcited(true)
    setCurrentCharacter(2)

    // 5번 이상 클릭하면 특별한 효과
    if (clickCount >= 4) {
      setClickMessage("와! 정말 열정적이시네요! 🎉✨ 투자도 이런 열정으로!")
      setClickAnimation("animate-bounce")
      // 파티클 효과 트리거
      triggerParticleEffect()
      setClickCount(0)
    }

    // 3초 후 메시지 숨기기
    setTimeout(() => {
      setShowClickMessage(false)
      setClickAnimation("")
      setIsExcited(false)
    }, 3000)
  }

  const triggerParticleEffect = () => {
    // 파티클 효과를 위한 임시 요소들 생성
    const container = document.getElementById("character-container")
    if (!container) return

    for (let i = 0; i < 10; i++) {
      const particle = document.createElement("div")
      particle.className = "absolute w-2 h-2 bg-yellow-400 rounded-full animate-ping"
      particle.style.left = Math.random() * 100 + "%"
      particle.style.top = Math.random() * 100 + "%"
      particle.style.animationDelay = Math.random() * 2 + "s"
      container.appendChild(particle)

      // 3초 후 제거
      setTimeout(() => {
        if (container.contains(particle)) {
          container.removeChild(particle)
        }
      }, 3000)
    }
  }

  return (
    <div className="relative flex items-center justify-center" id="character-container">
      {/* 클릭 메시지 말풍선 */}
      {showClickMessage && (
        <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 z-20 animate-bounce">
          <div className="bg-gradient-to-r from-yellow-100 to-orange-100 rounded-lg px-6 py-3 shadow-xl border-2 border-yellow-300 relative max-w-xs">
            <p className="text-sm font-bold text-gray-800 text-center whitespace-nowrap overflow-hidden text-ellipsis">
              {clickMessage}
            </p>
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent border-t-yellow-300"></div>
            </div>
          </div>
        </div>
      )}

      {/* 일반 말풍선 */}
      {isWaving && !showClickMessage && (
        <div className="absolute -top-16 left-1/2 transform -translate-x-1/2 z-10 animate-bounce">
          <div className="bg-white rounded-lg px-4 py-2 shadow-lg border-2 border-blue-200 relative">
            <p className="text-sm font-medium text-gray-800 whitespace-nowrap">클릭해보세요! 🖱️</p>
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent border-t-white"></div>
            </div>
          </div>
        </div>
      )}

      {/* 캐릭터 컨테이너 */}
      <div
        className={`relative transition-all duration-1000 cursor-pointer hover:scale-110 ${
          isFloating ? "transform -translate-y-2" : "transform translate-y-2"
        } ${isWaving || showClickMessage ? "scale-110" : "scale-100"} ${clickAnimation}`}
        style={{
          filter: "drop-shadow(0 10px 20px rgba(0, 0, 0, 0.1))",
        }}
        onClick={handleCharacterClick}
      >
        {/* 클릭 효과 링 */}
        {showClickMessage && (
          <div className="absolute inset-0 rounded-full border-4 border-yellow-400 animate-ping opacity-75"></div>
        )}

        {/* 캐릭터 이미지 */}
        <div className="relative">
          <img
            src={`/images/giga-buffett-character${currentCharacter === 2 ? "-2" : ""}.svg`}
            alt="기가 버핏 캐릭터"
            className={`w-80 h-80 transition-all duration-500 ${
              showClickMessage ? "animate-wiggle" : isWaving ? "animate-wiggle" : ""
            }`}
            style={{
              transform: showClickMessage ? "rotate(-5deg)" : isWaving ? "rotate(-5deg)" : "rotate(0deg)",
              transition: "transform 0.5s ease-in-out",
            }}
          />

          {/* 반짝이는 효과 */}
          <div className="absolute top-8 right-8 animate-ping">
            <div className="w-3 h-3 bg-yellow-400 rounded-full opacity-75"></div>
          </div>
          <div className="absolute top-16 right-12 animate-ping" style={{ animationDelay: "1s" }}>
            <div className="w-2 h-2 bg-blue-400 rounded-full opacity-75"></div>
          </div>
          <div className="absolute top-12 right-20 animate-ping" style={{ animationDelay: "2s" }}>
            <div className="w-2 h-2 bg-green-400 rounded-full opacity-75"></div>
          </div>

          {/* 클릭 시 추가 반짝이 효과 */}
          {showClickMessage && (
            <>
              <div className="absolute top-4 left-8 animate-ping">
                <div className="w-2 h-2 bg-pink-400 rounded-full opacity-75"></div>
              </div>
              <div className="absolute bottom-8 right-4 animate-ping" style={{ animationDelay: "0.5s" }}>
                <div className="w-3 h-3 bg-purple-400 rounded-full opacity-75"></div>
              </div>
              <div className="absolute bottom-12 left-12 animate-ping" style={{ animationDelay: "1.5s" }}>
                <div className="w-2 h-2 bg-red-400 rounded-full opacity-75"></div>
              </div>
            </>
          )}
        </div>

        {/* 그림자 */}
        <div
          className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-8 w-32 h-8 bg-gray-300 rounded-full opacity-30 blur-sm"
          style={{
            transform: `translateX(-50%) translateY(32px) scale(${isFloating ? "0.9" : "1.1"})`,
            transition: "transform 1s ease-in-out",
          }}
        ></div>
      </div>

      {/* 배경 원형 효과 */}
      <div className="absolute inset-0 -z-10">
        <div
          className={`w-96 h-96 bg-gradient-to-r from-blue-100 to-green-100 rounded-full opacity-20 ${
            showClickMessage ? "animate-spin" : "animate-spin-slow"
          }`}
        ></div>
      </div>

      {/* 클릭 카운터 표시 (5번 클릭에 가까워질 때) */}
      {clickCount > 2 && clickCount < 5 && (
        <div className="absolute -bottom-16 left-1/2 transform -translate-x-1/2">
          <div className="bg-purple-100 rounded-full px-3 py-1 text-xs font-bold text-purple-600 animate-pulse">
            {5 - clickCount}번 더 클릭하면 특별한 일이! ✨
          </div>
        </div>
      )}
    </div>
  )
}
