"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { TrendingUp, TrendingDown, Minus, Clock } from "lucide-react"

interface Signal {
  id: string
  symbol: string
  name: string
  action: "buy" | "sell" | "hold"
  confidence: number
  price: number
  targetPrice: number
  stopLoss: number
  timeframe: string
  strategy: string
  timestamp: string
  reason: string
}

const signals: Signal[] = [
  {
    id: "1",
    symbol: "AAPL",
    name: "Apple Inc.",
    action: "buy",
    confidence: 87,
    price: 175.5,
    targetPrice: 185.0,
    stopLoss: 168.0,
    timeframe: "1D",
    strategy: "AI 모멘텀",
    timestamp: "2분 전",
    reason: "강한 상승 모멘텀과 거래량 증가 감지",
  },
  {
    id: "2",
    symbol: "TSLA",
    name: "Tesla Inc.",
    action: "sell",
    confidence: 92,
    price: 245.8,
    targetPrice: 235.0,
    stopLoss: 252.0,
    timeframe: "4H",
    strategy: "평균회귀",
    timestamp: "5분 전",
    reason: "과매수 구간 진입, 조정 신호 포착",
  },
  {
    id: "3",
    symbol: "NVDA",
    name: "NVIDIA Corp.",
    action: "hold",
    confidence: 65,
    price: 420.3,
    targetPrice: 430.0,
    stopLoss: 410.0,
    timeframe: "1H",
    strategy: "볼린저 밴드",
    timestamp: "8분 전",
    reason: "중립 구간, 추가 신호 대기 중",
  },
  {
    id: "4",
    symbol: "MSFT",
    name: "Microsoft Corp.",
    action: "buy",
    confidence: 78,
    price: 378.9,
    targetPrice: 390.0,
    stopLoss: 370.0,
    timeframe: "2H",
    strategy: "고빈도 스캘핑",
    timestamp: "12분 전",
    reason: "단기 돌파 패턴 형성",
  },
]

export function TradingSignals() {
  const [selectedTimeframe, setSelectedTimeframe] = useState("ALL")

  const timeframes = ["ALL", "1M", "5M", "15M", "1H", "4H", "1D"]

  const getActionIcon = (action: string) => {
    switch (action) {
      case "buy":
        return <TrendingUp className="w-4 h-4" />
      case "sell":
        return <TrendingDown className="w-4 h-4" />
      case "hold":
        return <Minus className="w-4 h-4" />
      default:
        return <Minus className="w-4 h-4" />
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case "buy":
        return "bg-green-500 text-white"
      case "sell":
        return "bg-red-500 text-white"
      case "hold":
        return "bg-gray-500 text-white"
      default:
        return "bg-gray-500 text-white"
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "text-green-600"
    if (confidence >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">실시간 트레이딩 시그널</h2>
        <div className="flex items-center gap-3">
          <div className="flex bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-1">
            {timeframes.map((timeframe) => (
              <button
                key={timeframe}
                onClick={() => setSelectedTimeframe(timeframe)}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-all duration-200 ${
                  selectedTimeframe === timeframe
                    ? "bg-blue-500 text-white shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                }`}
              >
                {timeframe}
              </button>
            ))}
          </div>
          <Badge className="bg-green-100 text-green-800 border-green-200 animate-pulse">실시간 업데이트</Badge>
        </div>
      </div>

      {/* Signal Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">매수 신호</p>
                <p className="text-2xl font-bold text-green-900">2</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">매도 신호</p>
                <p className="text-2xl font-bold text-red-900">1</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900/20 dark:to-gray-800/20 border-gray-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">관망 신호</p>
                <p className="text-2xl font-bold text-gray-900">1</p>
              </div>
              <Minus className="w-8 h-8 text-gray-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Signals List */}
      <div className="space-y-4">
        {signals.map((signal) => (
          <Card
            key={signal.id}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all duration-300"
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-full ${getActionColor(signal.action)}`}>
                    {getActionIcon(signal.action)}
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{signal.symbol}</h3>
                      <Badge variant="outline" className="text-xs">
                        {signal.timeframe}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {signal.strategy}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{signal.name}</p>
                    <p className="text-xs text-gray-500 mt-1">{signal.reason}</p>
                  </div>
                </div>

                <div className="text-right">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">{signal.timestamp}</span>
                  </div>
                  <div className={`text-lg font-bold ${getConfidenceColor(signal.confidence)}`}>
                    신뢰도 {signal.confidence}%
                  </div>
                  <Progress value={signal.confidence} className="w-24 h-2 mt-1" />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="text-center">
                  <p className="text-sm text-gray-500">현재가</p>
                  <p className="text-lg font-semibold">${signal.price}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">목표가</p>
                  <p className="text-lg font-semibold text-green-600">${signal.targetPrice}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">손절가</p>
                  <p className="text-lg font-semibold text-red-600">${signal.stopLoss}</p>
                </div>
                <div className="text-center">
                  <Button
                    className={`w-full ${
                      signal.action === "buy"
                        ? "bg-green-500 hover:bg-green-600"
                        : signal.action === "sell"
                          ? "bg-red-500 hover:bg-red-600"
                          : "bg-gray-500 hover:bg-gray-600"
                    } text-white`}
                  >
                    {signal.action === "buy" && "매수 실행"}
                    {signal.action === "sell" && "매도 실행"}
                    {signal.action === "hold" && "관망"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
