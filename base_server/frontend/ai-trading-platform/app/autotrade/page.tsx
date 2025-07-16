"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { StrategyList } from "@/components/autotrade/strategy-list"
import { BacktestResults } from "@/components/autotrade/backtest-results"
import { TradingSignals } from "@/components/autotrade/trading-signals"
import { RiskManagement } from "@/components/autotrade/risk-management"
import { Bot, TrendingUp, Shield, BarChart3, Play, Pause } from "lucide-react"

export default function AutoTradePage() {
  const [isTrading, setIsTrading] = useState(false)

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            자동매매 시스템
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">AI 기반 자동매매 전략으로 24/7 스마트 트레이딩</p>
        </div>
        <div className="flex items-center gap-4">
          <Badge
            variant={isTrading ? "default" : "secondary"}
            className={`px-4 py-2 text-sm font-medium ${
              isTrading ? "bg-green-500 text-white animate-pulse" : "bg-gray-200 text-gray-700"
            }`}
          >
            {isTrading ? "거래 중" : "대기 중"}
          </Badge>
          <Button
            onClick={() => setIsTrading(!isTrading)}
            className={`px-6 py-2 font-medium transition-all duration-300 ${
              isTrading ? "bg-red-500 hover:bg-red-600 text-white" : "bg-green-500 hover:bg-green-600 text-white"
            }`}
          >
            {isTrading ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                정지
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                시작
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-400">활성 전략</p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">8</p>
              </div>
              <Bot className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">오늘 수익률</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100">+2.34%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600 dark:text-purple-400">총 거래</p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">156</p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600 dark:text-orange-400">리스크 점수</p>
                <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">7.2/10</p>
              </div>
              <Shield className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="strategies" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
          <TabsTrigger
            value="strategies"
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            전략 관리
          </TabsTrigger>
          <TabsTrigger
            value="signals"
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            트레이딩 시그널
          </TabsTrigger>
          <TabsTrigger
            value="backtest"
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            백테스트
          </TabsTrigger>
          <TabsTrigger
            value="risk"
            className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            리스크 관리
          </TabsTrigger>
        </TabsList>

        <TabsContent value="strategies" className="space-y-6">
          <StrategyList />
        </TabsContent>

        <TabsContent value="signals" className="space-y-6">
          <TradingSignals />
        </TabsContent>

        <TabsContent value="backtest" className="space-y-6">
          <BacktestResults />
        </TabsContent>

        <TabsContent value="risk" className="space-y-6">
          <RiskManagement />
        </TabsContent>
      </Tabs>
    </div>
  )
}
