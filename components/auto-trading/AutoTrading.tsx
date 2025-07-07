"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BoltIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  CheckCircleIcon,
  EyeIcon,
  PlayIcon,
  PauseIcon,
  CogIcon,
} from "@heroicons/react/24/outline"

const mockStrategies = [
  {
    id: "1",
    name: "보수적 가치투자 전략",
    description: "워렌 버핏 스타일의 장기 가치투자",
    philosophy: "우량 기업을 저평가된 가격에 매수하여 장기 보유",
    status: "active",
    performance: "+12.5%",
    trades: 23,
    winRate: "78%",
    lastTrade: "2024-01-15 14:30",
    rules: ["P/E 비율 15 이하", "부채비율 50% 이하", "ROE 15% 이상", "배당수익률 3% 이상"],
  },
  {
    id: "2",
    name: "성장주 모멘텀 전략",
    description: "피터 린치 스타일의 성장주 투자",
    philosophy: "높은 성장 잠재력을 가진 기업에 집중 투자",
    status: "paused",
    performance: "+8.3%",
    trades: 45,
    winRate: "65%",
    lastTrade: "2024-01-14 11:20",
    rules: ["매출 성장률 20% 이상", "PEG 비율 1.5 이하", "시가총액 1조원 이상", "기술주 우선 선택"],
  },
]

const mockTradeHistory = [
  {
    id: "1",
    symbol: "AAPL",
    action: "BUY",
    quantity: 10,
    price: 175.43,
    timestamp: "2024-01-15 14:30",
    reason: "P/E 비율이 15.2로 기준치 이하이며, 최근 실적 발표가 양호함. 배당수익률 3.2%로 안정적 수익 기대.",
    strategy: "보수적 가치투자 전략",
    profit: "+$543.20",
    status: "completed",
  },
  {
    id: "2",
    symbol: "GOOGL",
    action: "SELL",
    quantity: 5,
    price: 2734.56,
    timestamp: "2024-01-14 16:45",
    reason: "목표 수익률 15% 달성. 최근 광고 시장 불확실성으로 인한 리스크 관리 차원에서 일부 매도.",
    strategy: "성장주 모멘텀 전략",
    profit: "+$1,234.50",
    status: "completed",
  },
  {
    id: "3",
    symbol: "TSLA",
    action: "BUY",
    quantity: 8,
    price: 234.67,
    timestamp: "2024-01-14 11:20",
    reason: "전기차 시장 성장률 25% 유지, 자율주행 기술 발전으로 장기 성장 전망 긍정적.",
    strategy: "성장주 모멘텀 전략",
    profit: "+$892.40",
    status: "completed",
  },
]

export default function AutoTrading() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null)
  const [showTradeHistory, setShowTradeHistory] = useState(false)
  const [showCreateStrategy, setShowCreateStrategy] = useState(false)
  const [chatInput, setChatInput] = useState("")

  const handleCreateStrategy = () => {
    setShowCreateStrategy(true)
  }

  const handleChatSubmit = () => {
    if (chatInput.trim()) {
      // AI와 대화하여 전략 생성
      console.log("AI 전략 생성:", chatInput)
      setChatInput("")
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">자동매매</h1>
          <p className="text-gray-300">AI가 당신의 투자 철학에 맞는 자동매매 전략을 실행합니다</p>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={() => setShowTradeHistory(true)}
            variant="outline"
            className="bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50 hover:text-white hover:border-gray-600"
          >
            <ChartBarIcon className="w-4 h-4 mr-2" />
            거래 내역
          </Button>
          <Button
            onClick={handleCreateStrategy}
            className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white shadow-lg"
          >
            <BoltIcon className="w-4 h-4 mr-2" />새 전략 만들기
          </Button>
        </div>
      </div>

      {/* 전략 카드들 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {mockStrategies.map((strategy) => (
          <Card
            key={strategy.id}
            className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 shadow-xl hover:shadow-2xl hover:bg-gray-900/70 transition-all duration-300"
          >
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-3 h-3 rounded-full ${strategy.status === "active" ? "bg-green-500" : "bg-yellow-500"} animate-pulse`}
                  ></div>
                  <CardTitle className="text-white">{strategy.name}</CardTitle>
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSelectedStrategy(strategy.id)}
                    className="bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    className={`${strategy.status === "active" ? "bg-red-500 hover:bg-red-600" : "bg-green-500 hover:bg-green-600"}`}
                  >
                    {strategy.status === "active" ? (
                      <PauseIcon className="w-4 h-4" />
                    ) : (
                      <PlayIcon className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-300">{strategy.description}</p>

              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/30">
                <h4 className="text-sm font-semibold text-white mb-2">투자 철학</h4>
                <p className="text-gray-300 text-sm">{strategy.philosophy}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{strategy.performance}</div>
                  <div className="text-xs text-gray-400">총 수익률</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{strategy.winRate}</div>
                  <div className="text-xs text-gray-400">승률</div>
                </div>
              </div>

              <div className="flex justify-between text-sm text-gray-400">
                <span>총 거래: {strategy.trades}회</span>
                <span>최근 거래: {strategy.lastTrade}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* AI 전략 생성 모달 */}
      {showCreateStrategy && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl mx-4 bg-gray-900/95 backdrop-blur-sm border border-gray-800/50 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-white flex items-center space-x-2">
                <ChatBubbleLeftRightIcon className="w-5 h-5" />
                <span>AI와 함께 투자 전략 만들기</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/30">
                <p className="text-gray-300 text-sm mb-4">
                  AI에게 당신의 투자 철학과 선호하는 투자 스타일을 설명해주세요. 예: "안정적인 배당주 중심으로
                  장기투자하고 싶어요" 또는 "기술주 위주로 성장성 높은 종목에 투자하고 싶습니다"
                </p>

                <div className="space-y-4">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="예: 저는 위험을 최소화하면서도 꾸준한 수익을 원합니다. 배당주와 우량주 중심으로 포트폴리오를 구성하고, P/E 비율이 낮은 종목을 선호합니다..."
                    className="w-full h-32 bg-gray-800/50 border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />

                  <div className="flex flex-wrap gap-2">
                    {[
                      "안정적인 배당주 투자",
                      "성장주 중심 포트폴리오",
                      "가치투자 전략",
                      "기술주 집중 투자",
                      "ESG 투자",
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => setChatInput(suggestion + "에 대한 자동매매 전략을 만들어주세요.")}
                        className="px-3 py-1 bg-gray-700/50 text-gray-300 rounded-full text-sm hover:bg-gray-600/50 transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateStrategy(false)}
                  className="flex-1 bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50"
                >
                  취소
                </Button>
                <Button
                  onClick={handleChatSubmit}
                  disabled={!chatInput.trim()}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                >
                  AI 전략 생성
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 거래 내역 모달 */}
      {showTradeHistory && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="w-full max-w-4xl mx-4 bg-gray-900/95 backdrop-blur-sm border border-gray-800/50 shadow-2xl max-h-[80vh] overflow-hidden">
            <CardHeader className="border-b border-gray-800/50">
              <div className="flex justify-between items-center">
                <CardTitle className="text-white">거래 내역</CardTitle>
                <Button
                  variant="ghost"
                  onClick={() => setShowTradeHistory(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0 overflow-y-auto">
              <div className="divide-y divide-gray-800/50">
                {mockTradeHistory.map((trade) => (
                  <div key={trade.id} className="p-6 hover:bg-gray-800/30 transition-colors">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-4">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            trade.action === "BUY" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                          }`}
                        >
                          {trade.action === "BUY" ? "↗" : "↘"}
                        </div>
                        <div>
                          <div className="text-white font-semibold">
                            {trade.action} {trade.symbol} x{trade.quantity}
                          </div>
                          <div className="text-gray-400 text-sm">{trade.timestamp}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-semibold">${trade.price.toFixed(2)}</div>
                        <div className="text-green-400 text-sm">{trade.profit}</div>
                      </div>
                    </div>

                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/30">
                      <div className="text-sm text-gray-300 mb-2">
                        <span className="text-blue-400 font-medium">전략:</span> {trade.strategy}
                      </div>
                      <div className="text-sm text-gray-300">
                        <span className="text-yellow-400 font-medium">거래 근거:</span> {trade.reason}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 전략 상세 모달 */}
      {selectedStrategy && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl mx-4 bg-gray-900/95 backdrop-blur-sm border border-gray-800/50 shadow-2xl">
            <CardHeader className="border-b border-gray-800/50">
              <div className="flex justify-between items-center">
                <CardTitle className="text-white">전략 상세 정보</CardTitle>
                <Button
                  variant="ghost"
                  onClick={() => setSelectedStrategy(null)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {(() => {
                const strategy = mockStrategies.find((s) => s.id === selectedStrategy)
                if (!strategy) return null

                return (
                  <>
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">{strategy.name}</h3>
                      <p className="text-gray-300">{strategy.description}</p>
                    </div>

                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/30">
                      <h4 className="text-white font-medium mb-3">매매 규칙</h4>
                      <div className="space-y-2">
                        {strategy.rules.map((rule, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <CheckCircleIcon className="w-4 h-4 text-green-400" />
                            <span className="text-gray-300 text-sm">{rule}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-xl font-bold text-green-400">{strategy.performance}</div>
                        <div className="text-xs text-gray-400">수익률</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-blue-400">{strategy.trades}</div>
                        <div className="text-xs text-gray-400">총 거래</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-purple-400">{strategy.winRate}</div>
                        <div className="text-xs text-gray-400">승률</div>
                      </div>
                    </div>

                    <div className="flex space-x-3">
                      <Button
                        variant="outline"
                        className="flex-1 bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50"
                      >
                        <CogIcon className="w-4 h-4 mr-2" />
                        설정 수정
                      </Button>
                      <Button
                        className={`flex-1 ${
                          strategy.status === "active"
                            ? "bg-red-500 hover:bg-red-600"
                            : "bg-green-500 hover:bg-green-600"
                        }`}
                      >
                        {strategy.status === "active" ? (
                          <>
                            <PauseIcon className="w-4 h-4 mr-2" />
                            일시정지
                          </>
                        ) : (
                          <>
                            <PlayIcon className="w-4 h-4 mr-2" />
                            시작
                          </>
                        )}
                      </Button>
                    </div>
                  </>
                )
              })()}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
