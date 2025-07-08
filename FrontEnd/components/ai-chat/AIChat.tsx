"use client"

import { useState, useRef, useEffect } from "react"
import { PaperAirplaneIcon, DocumentTextIcon, PlusIcon, TrashIcon } from "@heroicons/react/24/outline"
import { Button } from "@/components/ui/button"
import type { ChatMessage } from "../../types"

const suggestedQuestions = [
  "What stocks should I invest in for long-term growth?",
  "How should I diversify my portfolio?",
  "What's the current market sentiment?",
  "Should I buy or sell AAPL right now?",
  "Explain the P/E ratio in simple terms",
  "What are the risks of investing in tech stocks?",
  "Create an auto-trading strategy for me",
  "Analyze my portfolio performance",
]

const investorPersonalities = [
  {
    id: "buffett",
    name: "워렌 버핏",
    description: "가치투자의 대가",
    avatar: "🧓",
    style: "장기 가치투자, 기업 펀더멘털 중심",
  },
  {
    id: "lynch",
    name: "피터 린치",
    description: "성장주 투자 전문가",
    avatar: "👨‍💼",
    style: "성장주 발굴, 소비자 관점 투자",
  },
  {
    id: "graham",
    name: "벤저민 그레이엄",
    description: "증권분석의 아버지",
    avatar: "👴",
    style: "철저한 분석, 안전마진 중시",
  },
  {
    id: "ai",
    name: "기가 버핏 AI",
    description: "종합 투자 어드바이저",
    avatar: "🤖",
    style: "데이터 기반 맞춤형 조언",
  },
]

export default function AIChat() {
  const [chatSessions, setChatSessions] = useState([
    {
      id: "default",
      name: "기본 채팅",
      personality: "ai",
      messages: [
        {
          id: "1",
          type: "ai" as const,
          content:
            "안녕하세요! 저는 기가 버핏 AI입니다. 투자 분석, 포트폴리오 추천, 투자 전략에 대해 도움을 드릴 수 있습니다. 무엇을 도와드릴까요?",
          timestamp: new Date(),
        },
      ],
    },
  ])

  const [currentSessionId, setCurrentSessionId] = useState("default")
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const currentSession = chatSessions.find((s) => s.id === currentSessionId) || chatSessions[0]
  const currentPersonality =
    investorPersonalities.find((p) => p.id === currentSession.personality) || investorPersonalities[3]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentSession.messages])

  const createNewChat = (personalityId: string) => {
    const personality = investorPersonalities.find((p) => p.id === personalityId) || investorPersonalities[3]
    const newSession = {
      id: Date.now().toString(),
      name: `${personality.name}와의 대화`,
      personality: personalityId,
      messages: [
        {
          id: Date.now().toString(),
          type: "ai" as const,
          content: getPersonalityGreeting(personalityId),
          timestamp: new Date(),
        },
      ],
    }

    setChatSessions((prev) => [...prev, newSession])
    setCurrentSessionId(newSession.id)
  }

  const getPersonalityGreeting = (personalityId: string): string => {
    switch (personalityId) {
      case "buffett":
        return "안녕하세요! 워렌 버핏입니다. 장기적 관점에서 우량 기업에 투자하는 것이 성공의 열쇠입니다. 어떤 투자에 대해 이야기해볼까요?"
      case "lynch":
        return "피터 린치입니다! 일상에서 발견할 수 있는 훌륭한 투자 기회들이 많습니다. 어떤 기업이나 산업에 관심이 있으신가요?"
      case "graham":
        return "벤저민 그레이엄입니다. 철저한 분석과 안전마진을 통해 리스크를 최소화하는 것이 중요합니다. 분석하고 싶은 종목이 있나요?"
      default:
        return "안녕하세요! 기가 버핏 AI입니다. 투자에 관한 모든 것을 도와드리겠습니다."
    }
  }

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: content.trim(),
      timestamp: new Date(),
    }

    setChatSessions((prev) =>
      prev.map((session) =>
        session.id === currentSessionId ? { ...session, messages: [...session.messages, userMessage] } : session,
      ),
    )

    setInputValue("")
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: generatePersonalityResponse(content, currentSession.personality),
        timestamp: new Date(),
      }

      setChatSessions((prev) =>
        prev.map((session) =>
          session.id === currentSessionId ? { ...session, messages: [...session.messages, aiResponse] } : session,
        ),
      )

      setIsTyping(false)
    }, 1500)
  }

  const generatePersonalityResponse = (userInput: string, personalityId: string): string => {
    const input = userInput.toLowerCase()

    const baseResponses = {
      buffett: {
        portfolio:
          "포트폴리오는 마치 야구와 같습니다. 좋은 공이 올 때까지 기다렸다가 확신이 설 때 크게 스윙하는 것이죠. 분산투자보다는 이해할 수 있는 우량 기업에 집중 투자하는 것을 추천합니다.",
        risk: "리스크는 자신이 무엇을 하고 있는지 모르는 데서 나옵니다. 기업을 이해하고, 합리적인 가격에 사면 리스크는 크게 줄어듭니다.",
        default:
          "투자에서 가장 중요한 것은 인내심입니다. 시장의 단기 변동에 휘둘리지 말고, 좋은 기업을 합리적인 가격에 사서 오래 보유하세요.",
      },
      lynch: {
        portfolio:
          "당신이 잘 아는 분야부터 시작하세요. 일상에서 사용하는 제품이나 서비스를 만드는 회사들을 살펴보세요. 소비자로서의 경험이 투자의 출발점이 될 수 있습니다.",
        growth: "성장주를 찾을 때는 PEG 비율을 보세요. 성장률 대비 저평가된 주식을 찾는 것이 핵심입니다.",
        default: "투자는 복잡할 필요가 없습니다. 좋은 회사를 찾고, 그 회사가 계속 성장할 수 있는지 확인하세요.",
      },
      graham: {
        analysis:
          "철저한 재무제표 분석이 필요합니다. 부채비율, 유동비율, ROE 등을 꼼꼼히 살펴보고 안전마진을 확보하세요.",
        value:
          "내재가치 대비 현재 주가가 충분히 할인되어 있는지 확인하세요. 시장의 감정에 휘둘리지 말고 숫자에 집중하세요.",
        default: "투자자는 기업의 일부 소유자라는 마음가짐으로 접근해야 합니다. 감정이 아닌 분석에 기반해 투자하세요.",
      },
    }

    const responses = baseResponses[personalityId as keyof typeof baseResponses]

    if (!responses) {
      return "죄송합니다. 해당 투자자의 관점에서 답변을 드릴 수 없습니다."
    }

    if (input.includes("portfolio") || input.includes("포트폴리오")) {
      return responses.portfolio || responses.default
    } else if (input.includes("risk") || input.includes("위험") || input.includes("리스크")) {
      return responses.risk || responses.default
    } else if (input.includes("growth") || input.includes("성장")) {
      return responses.growth || responses.default
    } else if (input.includes("analysis") || input.includes("분석")) {
      return responses.analysis || responses.default
    } else if (input.includes("value") || input.includes("가치")) {
      return responses.value || responses.default
    } else {
      return responses.default
    }
  }

  const deleteSession = (sessionId: string) => {
    if (chatSessions.length > 1) {
      setChatSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (currentSessionId === sessionId) {
        setCurrentSessionId(chatSessions.find((s) => s.id !== sessionId)?.id || chatSessions[0].id)
      }
    }
  }

  const handleSummarize = () => {
    const lastAIMessage = currentSession.messages.filter((m) => m.type === "ai").pop()
    if (lastAIMessage) {
      const summary = `📋 대화 요약: ${lastAIMessage.content.substring(0, 100)}...`
      const summaryMessage: ChatMessage = {
        id: Date.now().toString(),
        type: "ai",
        content: summary,
        timestamp: new Date(),
      }

      setChatSessions((prev) =>
        prev.map((session) =>
          session.id === currentSessionId ? { ...session, messages: [...session.messages, summaryMessage] } : session,
        ),
      )
    }
  }

  return (
    <div className="flex h-[calc(100vh-12rem)] animate-fade-in">
      {/* 채팅 세션 사이드바 */}
      <div className="w-80 bg-black/50 backdrop-blur-sm border-r border-gray-800/50 flex flex-col">
        {/* 새 채팅 버튼 */}
        <div className="p-4 border-b border-gray-800/50">
          <div className="relative group">
            <Button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white flex items-center justify-center space-x-2">
              <PlusIcon className="w-4 h-4" />
              <span>새 채팅</span>
            </Button>

            {/* 투자자 선택 드롭다운 */}
            <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900/95 backdrop-blur-sm border border-gray-700/50 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
              {investorPersonalities.map((personality) => (
                <button
                  key={personality.id}
                  onClick={() => createNewChat(personality.id)}
                  className="w-full p-3 text-left hover:bg-gray-800/50 first:rounded-t-lg last:rounded-b-lg transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{personality.avatar}</span>
                    <div>
                      <div className="text-white font-medium">{personality.name}</div>
                      <div className="text-gray-400 text-xs">{personality.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 채팅 세션 목록 */}
        <div className="flex-1 overflow-y-auto">
          {chatSessions.map((session) => (
            <div
              key={session.id}
              className={`p-4 border-b border-gray-800/30 cursor-pointer transition-all duration-200 ${
                currentSessionId === session.id ? "bg-blue-500/20 border-l-4 border-l-blue-500" : "hover:bg-gray-800/30"
              }`}
              onClick={() => setCurrentSessionId(session.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <span className="text-xl">
                    {investorPersonalities.find((p) => p.id === session.personality)?.avatar || "🤖"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-white font-medium truncate">{session.name}</div>
                    <div className="text-gray-400 text-xs truncate">
                      {session.messages[session.messages.length - 1]?.content.substring(0, 30)}...
                    </div>
                  </div>
                </div>
                {chatSessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteSession(session.id)
                    }}
                    className="text-gray-500 hover:text-red-400 transition-colors p-1"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 메인 채팅 영역 */}
      <div className="flex-1 flex flex-col">
        {/* 헤더 */}
        <div className="bg-black/50 backdrop-blur-sm border-b border-gray-800/50 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{currentPersonality.avatar}</span>
              <div>
                <h2 className="text-lg font-semibold text-white">{currentPersonality.name}</h2>
                <p className="text-sm text-gray-400">{currentPersonality.style}</p>
              </div>
            </div>
            <button
              onClick={handleSummarize}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all duration-200 shadow-lg"
            >
              <DocumentTextIcon className="h-4 w-4 mr-1" />
              요약
            </button>
          </div>
        </div>

        {/* 메시지 */}
        <div className="flex-1 overflow-y-auto bg-gray-900/30 backdrop-blur-sm px-6 py-4 space-y-4">
          {currentSession.messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                  message.type === "user"
                    ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg"
                    : "bg-gray-800/70 backdrop-blur-sm text-white shadow-lg border border-gray-700/30"
                }`}
              >
                <p className="text-sm leading-relaxed">{message.content}</p>
                <p className={`text-xs mt-2 ${message.type === "user" ? "text-blue-100" : "text-gray-400"}`}>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-gray-800/70 backdrop-blur-sm text-white shadow-lg border border-gray-700/30 max-w-xs lg:max-w-md px-4 py-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                  <span className="text-sm text-gray-300">{currentPersonality.name}이 입력 중...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 제안 질문 */}
        <div className="bg-black/50 backdrop-blur-sm border-t border-gray-800/50 px-6 py-3">
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.slice(0, 4).map((question, index) => (
              <button
                key={index}
                onClick={() => handleSendMessage(question)}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-800/50 text-gray-300 hover:bg-gray-700/50 hover:text-white transition-colors border border-gray-700/30"
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        {/* 입력 */}
        <div className="bg-black/50 backdrop-blur-sm border-t border-gray-800/50 px-6 py-4 tutorial-target-chat-input">
          <div className="flex items-center space-x-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSendMessage(inputValue)}
              placeholder={`${currentPersonality.name}에게 투자에 대해 질문해보세요...`}
              className="flex-1 border border-gray-700/50 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-800/50 text-white placeholder-gray-400"
            />
            <button
              onClick={() => handleSendMessage(inputValue)}
              disabled={!inputValue.trim() || isTyping}
              className="inline-flex items-center px-4 py-3 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
            >
              <PaperAirplaneIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
