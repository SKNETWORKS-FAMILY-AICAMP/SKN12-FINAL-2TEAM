"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts"
import { Shield, AlertTriangle, TrendingDown, BarChart3 } from "lucide-react"

interface RiskReportProps {
  period: string
}

const drawdownData = [
  { date: "2024-01", drawdown: 0 },
  { date: "2024-02", drawdown: -2.1 },
  { date: "2024-03", drawdown: -1.5 },
  { date: "2024-04", drawdown: -5.2 },
  { date: "2024-05", drawdown: -3.8 },
  { date: "2024-06", drawdown: -2.1 },
  { date: "2024-07", drawdown: -8.3 },
]

const riskMetrics = [
  { metric: "변동성", value: 85, fullMark: 100 },
  { metric: "집중도", value: 65, fullMark: 100 },
  { metric: "유동성", value: 90, fullMark: 100 },
  { metric: "신용도", value: 95, fullMark: 100 },
  { metric: "지역분산", value: 70, fullMark: 100 },
  { metric: "섹터분산", value: 75, fullMark: 100 },
]

export function RiskReport({ period }: RiskReportProps) {
  return (
    <div className="space-y-6">
      {/* Risk Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">VaR (95%)</p>
                <p className="text-2xl font-bold text-red-900">₩2.4M</p>
                <p className="text-xs text-red-600">일일 최대 예상 손실</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">최대 낙폭</p>
                <p className="text-2xl font-bold text-orange-900">-8.3%</p>
                <p className="text-xs text-orange-600">지난 {period} 최대 하락</p>
              </div>
              <TrendingDown className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-600">베타</p>
                <p className="text-2xl font-bold text-yellow-900">0.87</p>
                <p className="text-xs text-yellow-600">시장 대비 변동성</p>
              </div>
              <BarChart3 className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">리스크 점수</p>
                <p className="text-2xl font-bold text-blue-900">7.2/10</p>
                <p className="text-xs text-blue-600">종합 리스크 평가</p>
              </div>
              <Shield className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Drawdown Chart */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-red-500" />
            낙폭 분석
          </CardTitle>
          <CardDescription>시간별 포트폴리오 낙폭 추이 ({period} 기준)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={drawdownData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => [`${value}%`, "낙폭"]}
                  labelFormatter={(label) => `기간: ${label}`}
                />
                <Area type="monotone" dataKey="drawdown" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Risk Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>리스크 프로필</CardTitle>
            <CardDescription>다차원 리스크 분석</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={riskMetrics}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar
                    name="리스크 점수"
                    dataKey="value"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>섹터별 리스크 분산</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { sector: "기술", risk: 85, allocation: 35, color: "bg-red-500" },
              { sector: "금융", risk: 45, allocation: 20, color: "bg-yellow-500" },
              { sector: "헬스케어", risk: 35, allocation: 15, color: "bg-green-500" },
              { sector: "소비재", risk: 40, allocation: 12, color: "bg-yellow-500" },
              { sector: "에너지", risk: 75, allocation: 10, color: "bg-orange-500" },
              { sector: "기타", risk: 30, allocation: 8, color: "bg-green-500" },
            ].map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{item.sector}</span>
                  <div className="flex items-center gap-2">
                    <Badge
                      className={`${
                        item.risk >= 70
                          ? "bg-red-100 text-red-800 border-red-200"
                          : item.risk >= 50
                            ? "bg-yellow-100 text-yellow-800 border-yellow-200"
                            : "bg-green-100 text-green-800 border-green-200"
                      } border`}
                    >
                      {item.risk >= 70 ? "높음" : item.risk >= 50 ? "중간" : "낮음"}
                    </Badge>
                    <span className="text-sm text-gray-500">{item.allocation}%</span>
                  </div>
                </div>
                <Progress value={item.risk} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Risk Alerts */}
      <Card className="bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 border-orange-200 dark:border-orange-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-orange-800 dark:text-orange-200">
            <AlertTriangle className="w-5 h-5" />
            리스크 경고
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-red-200">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">높은 섹터 집중도</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  기술주 비중이 35%로 과도하게 집중되어 있습니다.
                </p>
              </div>
              <Badge className="bg-red-100 text-red-800 border-red-200 ml-auto">위험</Badge>
            </div>

            <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-yellow-200">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">변동성 증가</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  최근 1주일간 포트폴리오 변동성이 평균 대비 25% 증가했습니다.
                </p>
              </div>
              <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200 ml-auto">주의</Badge>
            </div>

            <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-green-200">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">유동성 양호</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  포트폴리오 내 모든 자산의 유동성이 충분합니다.
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
