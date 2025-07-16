"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Shield, AlertTriangle, DollarSign } from "lucide-react"

export function RiskManagement() {
  const [maxDrawdown, setMaxDrawdown] = useState([15])
  const [positionSize, setPositionSize] = useState([25])
  const [stopLoss, setStopLoss] = useState([5])
  const [riskPerTrade, setRiskPerTrade] = useState([2])
  const [autoStopLoss, setAutoStopLoss] = useState(true)
  const [portfolioHedging, setPortfolioHedging] = useState(false)

  const riskMetrics = [
    {
      title: "포트폴리오 VaR (95%)",
      value: "₩2.4M",
      percentage: 4.8,
      status: "양호",
      color: "green",
    },
    {
      title: "최대 낙폭 (1개월)",
      value: "-8.3%",
      percentage: 55,
      status: "주의",
      color: "yellow",
    },
    {
      title: "베타 (시장 대비)",
      value: "0.87",
      percentage: 87,
      status: "안정",
      color: "green",
    },
    {
      title: "샤프 비율",
      value: "1.84",
      percentage: 92,
      status: "우수",
      color: "green",
    },
  ]

  const getStatusColor = (color: string) => {
    switch (color) {
      case "green":
        return "text-green-600 bg-green-100 border-green-200"
      case "yellow":
        return "text-yellow-600 bg-yellow-100 border-yellow-200"
      case "red":
        return "text-red-600 bg-red-100 border-red-200"
      default:
        return "text-gray-600 bg-gray-100 border-gray-200"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">리스크 관리</h2>
        <Button className="bg-blue-500 hover:bg-blue-600 text-white">
          <Shield className="w-4 h-4 mr-2" />
          설정 저장
        </Button>
      </div>

      {/* Risk Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {riskMetrics.map((metric, index) => (
          <Card
            key={index}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all duration-300"
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-gray-500" />
                  <Badge className={`${getStatusColor(metric.color)} border text-xs`}>{metric.status}</Badge>
                </div>
              </div>
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">{metric.title}</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">{metric.value}</p>
              <Progress value={metric.percentage} className="h-2" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Risk Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Position Management */}
        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-blue-500" />
              포지션 관리
            </CardTitle>
            <CardDescription>개별 포지션 크기 및 리스크 제한 설정</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">최대 포지션 크기</label>
                <span className="text-sm font-semibold text-blue-600">{positionSize[0]}%</span>
              </div>
              <Slider
                value={positionSize}
                onValueChange={setPositionSize}
                max={50}
                min={5}
                step={5}
                className="w-full"
              />
              <p className="text-xs text-gray-500">단일 종목에 투자할 수 있는 최대 비중</p>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">거래당 리스크</label>
                <span className="text-sm font-semibold text-blue-600">{riskPerTrade[0]}%</span>
              </div>
              <Slider
                value={riskPerTrade}
                onValueChange={setRiskPerTrade}
                max={10}
                min={0.5}
                step={0.5}
                className="w-full"
              />
              <p className="text-xs text-gray-500">단일 거래에서 감수할 수 있는 최대 손실 비율</p>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">손절매 비율</label>
                <span className="text-sm font-semibold text-blue-600">-{stopLoss[0]}%</span>
              </div>
              <Slider value={stopLoss} onValueChange={setStopLoss} max={20} min={1} step={1} className="w-full" />
              <p className="text-xs text-gray-500">자동 손절매가 실행되는 손실 비율</p>
            </div>
          </CardContent>
        </Card>

        {/* Portfolio Risk */}
        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-purple-500" />
              포트폴리오 리스크
            </CardTitle>
            <CardDescription>전체 포트폴리오 리스크 제한 및 보호 설정</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">최대 낙폭 한계</label>
                <span className="text-sm font-semibold text-purple-600">-{maxDrawdown[0]}%</span>
              </div>
              <Slider value={maxDrawdown} onValueChange={setMaxDrawdown} max={30} min={5} step={5} className="w-full" />
              <p className="text-xs text-gray-500">이 수준에 도달하면 모든 거래를 중단합니다</p>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">자동 손절매</h4>
                <p className="text-xs text-gray-500">설정된 손실 비율에서 자동으로 포지션 청산</p>
              </div>
              <Switch
                checked={autoStopLoss}
                onCheckedChange={setAutoStopLoss}
                className="data-[state=checked]:bg-blue-500"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">포트폴리오 헤징</h4>
                <p className="text-xs text-gray-500">시장 하락 시 자동으로 헤징 포지션 생성</p>
              </div>
              <Switch
                checked={portfolioHedging}
                onCheckedChange={setPortfolioHedging}
                className="data-[state=checked]:bg-blue-500"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Alerts */}
      <Card className="bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 border-orange-200 dark:border-orange-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-orange-800 dark:text-orange-200">
            <AlertTriangle className="w-5 h-5" />
            리스크 알림
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-orange-200">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">포트폴리오 집중도 경고</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  기술주 비중이 40%를 초과했습니다. 분산투자를 고려하세요.
                </p>
              </div>
              <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200 ml-auto">주의</Badge>
            </div>

            <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-orange-200">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">리스크 관리 양호</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  현재 포트폴리오 리스크가 목표 범위 내에 있습니다.
                </p>
              </div>
              <Badge className="bg-green-100 text-green-800 border-green-200 ml-auto">양호</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
