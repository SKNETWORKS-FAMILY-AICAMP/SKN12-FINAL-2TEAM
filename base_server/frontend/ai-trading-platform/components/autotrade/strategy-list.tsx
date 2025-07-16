"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Progress } from "@/components/ui/progress"
import { Bot, TrendingUp, TrendingDown, Activity, Settings, Play, Pause } from "lucide-react"

interface Strategy {
  id: string
  name: string
  description: string
  type: "momentum" | "mean_reversion" | "arbitrage" | "scalping"
  isActive: boolean
  performance: number
  winRate: number
  totalTrades: number
  riskLevel: "low" | "medium" | "high"
  allocation: number
}

const strategies: Strategy[] = [
  {
    id: "1",
    name: "AI 모멘텀 전략",
    description: "머신러닝 기반 모멘텀 추세 추종 전략",
    type: "momentum",
    isActive: true,
    performance: 18.5,
    winRate: 67,
    totalTrades: 234,
    riskLevel: "medium",
    allocation: 35,
  },
  {
    id: "2",
    name: "평균회귀 전략",
    description: "통계적 평균회귀를 이용한 역추세 전략",
    type: "mean_reversion",
    isActive: true,
    performance: 12.3,
    winRate: 72,
    totalTrades: 156,
    riskLevel: "low",
    allocation: 25,
  },
  {
    id: "3",
    name: "볼린저 밴드 전략",
    description: "볼린저 밴드 기반 변동성 돌파 전략",
    type: "momentum",
    isActive: false,
    performance: 8.7,
    winRate: 58,
    totalTrades: 89,
    riskLevel: "medium",
    allocation: 20,
  },
  {
    id: "4",
    name: "고빈도 스캘핑",
    description: "초단타 고빈도 거래 전략",
    type: "scalping",
    isActive: true,
    performance: 24.1,
    winRate: 64,
    totalTrades: 1247,
    riskLevel: "high",
    allocation: 20,
  },
]

export function StrategyList() {
  const [strategyStates, setStrategyStates] = useState(strategies)

  const toggleStrategy = (id: string) => {
    setStrategyStates((prev) =>
      prev.map((strategy) => (strategy.id === id ? { ...strategy, isActive: !strategy.isActive } : strategy)),
    )
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case "low":
        return "text-green-600 bg-green-100 border-green-200"
      case "medium":
        return "text-yellow-600 bg-yellow-100 border-yellow-200"
      case "high":
        return "text-red-600 bg-red-100 border-red-200"
      default:
        return "text-gray-600 bg-gray-100 border-gray-200"
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "momentum":
        return <TrendingUp className="w-4 h-4" />
      case "mean_reversion":
        return <TrendingDown className="w-4 h-4" />
      case "scalping":
        return <Activity className="w-4 h-4" />
      default:
        return <Bot className="w-4 h-4" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">전략 관리</h2>
        <Button className="bg-blue-500 hover:bg-blue-600 text-white">
          <Bot className="w-4 h-4 mr-2" />새 전략 추가
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {strategyStates.map((strategy) => (
          <Card
            key={strategy.id}
            className={`transition-all duration-300 hover:shadow-lg ${
              strategy.isActive
                ? "border-blue-200 bg-blue-50/50 dark:bg-blue-900/10"
                : "border-gray-200 bg-white dark:bg-gray-800"
            }`}
          >
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-lg ${strategy.isActive ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-600"}`}
                  >
                    {getTypeIcon(strategy.type)}
                  </div>
                  <div>
                    <CardTitle className="text-lg font-semibold">{strategy.name}</CardTitle>
                    <CardDescription className="text-sm">{strategy.description}</CardDescription>
                  </div>
                </div>
                <Switch
                  checked={strategy.isActive}
                  onCheckedChange={() => toggleStrategy(strategy.id)}
                  className="data-[state=checked]:bg-blue-500"
                />
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Performance Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">+{strategy.performance}%</p>
                  <p className="text-xs text-gray-500">수익률</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{strategy.winRate}%</p>
                  <p className="text-xs text-gray-500">승률</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">{strategy.totalTrades}</p>
                  <p className="text-xs text-gray-500">총 거래</p>
                </div>
              </div>

              {/* Allocation */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">자금 배분</span>
                  <span className="font-medium">{strategy.allocation}%</span>
                </div>
                <Progress value={strategy.allocation} className="h-2" />
              </div>

              {/* Risk Level & Actions */}
              <div className="flex items-center justify-between pt-2">
                <Badge className={`${getRiskColor(strategy.riskLevel)} border`}>
                  {strategy.riskLevel === "low" && "낮은 위험"}
                  {strategy.riskLevel === "medium" && "중간 위험"}
                  {strategy.riskLevel === "high" && "높은 위험"}
                </Badge>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={strategy.isActive ? "destructive" : "default"}
                    size="sm"
                    onClick={() => toggleStrategy(strategy.id)}
                  >
                    {strategy.isActive ? (
                      <>
                        <Pause className="w-4 h-4 mr-1" />
                        정지
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-1" />
                        시작
                      </>
                    )}
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
