"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { BarChart3, TrendingUp, TrendingDown, Target } from "lucide-react"

interface TechnicalAnalysisProps {
  detailed?: boolean
}

const technicalData = [
  { time: "09:00", price: 2480, rsi: 45, volume: 120 },
  { time: "10:00", price: 2485, rsi: 52, volume: 135 },
  { time: "11:00", price: 2478, rsi: 48, volume: 142 },
  { time: "12:00", price: 2490, rsi: 58, volume: 128 },
  { time: "13:00", price: 2495, rsi: 62, volume: 156 },
  { time: "14:00", price: 2488, rsi: 55, volume: 148 },
  { time: "15:00", price: 2492, rsi: 59, volume: 162 },
]

const indicators = [
  {
    name: "RSI (14)",
    value: 59.2,
    signal: "중립",
    description: "과매수/과매도 구간 아님",
    color: "yellow",
  },
  {
    name: "MACD",
    value: 12.5,
    signal: "매수",
    description: "골든크로스 형성",
    color: "green",
  },
  {
    name: "볼린저 밴드",
    value: 75.3,
    signal: "매수",
    description: "하단 밴드 근처에서 반등",
    color: "green",
  },
  {
    name: "스토캐스틱",
    value: 42.8,
    signal: "중립",
    description: "중간 구간 위치",
    color: "yellow",
  },
  {
    name: "이동평균선",
    value: 85.6,
    signal: "매수",
    description: "20일선 상향 돌파",
    color: "green",
  },
  {
    name: "거래량",
    value: 68.4,
    signal: "보통",
    description: "평균 거래량 수준",
    color: "gray",
  },
]

const supportResistance = [
  { level: "저항선 3", price: 2520, strength: "강함", distance: 1.2 },
  { level: "저항선 2", price: 2505, strength: "보통", distance: 0.6 },
  { level: "저항선 1", price: 2498, strength: "약함", distance: 0.3 },
  { level: "현재가", price: 2492, strength: "-", distance: 0 },
  { level: "지지선 1", price: 2485, strength: "약함", distance: -0.3 },
  { level: "지지선 2", price: 2470, strength: "보통", distance: -0.9 },
  { level: "지지선 3", price: 2450, strength: "강함", distance: -1.7 },
]

export function TechnicalAnalysis({ detailed = false }: TechnicalAnalysisProps) {
  const getSignalColor = (signal: string) => {
    switch (signal.toLowerCase()) {
      case "매수":
        return "bg-green-100 text-green-700 border-green-200"
      case "매도":
        return "bg-red-100 text-red-700 border-red-200"
      case "중립":
      case "보통":
        return "bg-yellow-100 text-yellow-700 border-yellow-200"
      default:
        return "bg-gray-100 text-gray-700 border-gray-200"
    }
  }

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case "강함":
        return "text-red-600"
      case "보통":
        return "text-yellow-600"
      case "약함":
        return "text-green-600"
      default:
        return "text-gray-600"
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3 text-xl">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 text-white">
              <BarChart3 className="h-5 w-5" />
            </div>
            기술적 분석
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Price Chart */}
          <div className="bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-800 dark:to-slate-700 rounded-xl p-6 border border-gray-200 dark:border-gray-600">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">KOSPI 일중 차트</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={technicalData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6b7280" }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6b7280" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(255, 255, 255, 0.95)",
                      border: "none",
                      borderRadius: "12px",
                      boxShadow: "0 10px 25px rgba(0, 0, 0, 0.1)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#3b82f6"
                    strokeWidth={3}
                    dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Technical Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {indicators.map((indicator, index) => (
              <div
                key={index}
                className="p-4 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-gray-200 dark:border-gray-600"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-900 dark:text-white">{indicator.name}</h4>
                  <Badge variant="outline" className={`text-xs ${getSignalColor(indicator.signal)}`}>
                    {indicator.signal}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">{indicator.value.toFixed(1)}</div>
                  <Progress value={indicator.value} className="h-2" />
                  <p className="text-xs text-gray-600 dark:text-gray-400">{indicator.description}</p>
                </div>
              </div>
            ))}
          </div>

          {detailed && (
            <>
              {/* Support & Resistance */}
              <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Target className="h-5 w-5 text-blue-600" />
                    지지선 & 저항선
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {supportResistance.map((level, index) => (
                      <div
                        key={index}
                        className={`flex items-center justify-between p-3 rounded-lg ${
                          level.level === "현재가"
                            ? "bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-300 dark:border-blue-600"
                            : "bg-white dark:bg-slate-700 border border-gray-200 dark:border-gray-600"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            {level.level.includes("저항") && <TrendingUp className="h-4 w-4 text-red-500" />}
                            {level.level.includes("지지") && <TrendingDown className="h-4 w-4 text-green-500" />}
                            {level.level === "현재가" && <Target className="h-4 w-4 text-blue-500" />}
                            <span
                              className={`font-medium ${
                                level.level === "현재가"
                                  ? "text-blue-900 dark:text-blue-100"
                                  : "text-gray-900 dark:text-white"
                              }`}
                            >
                              {level.level}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <span className="font-bold text-gray-900 dark:text-white">
                            {level.price.toLocaleString()}
                          </span>
                          {level.strength !== "-" && (
                            <Badge variant="outline" className={`text-xs ${getStrengthColor(level.strength)}`}>
                              {level.strength}
                            </Badge>
                          )}
                          {level.distance !== 0 && (
                            <span className={`text-sm ${level.distance > 0 ? "text-red-600" : "text-green-600"}`}>
                              {level.distance > 0 ? "+" : ""}
                              {level.distance.toFixed(1)}%
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Trading Signals Summary */}
              <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-700">
                <CardHeader>
                  <CardTitle className="text-lg text-green-900 dark:text-green-100">종합 매매 신호</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600 mb-2">매수</div>
                      <p className="text-sm text-green-700 dark:text-green-300">3개 지표</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-yellow-600 mb-2">중립</div>
                      <p className="text-sm text-yellow-700 dark:text-yellow-300">2개 지표</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-red-600 mb-2">매도</div>
                      <p className="text-sm text-red-700 dark:text-red-300">1개 지표</p>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-white dark:bg-slate-700 rounded-lg border border-green-200 dark:border-green-700">
                    <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">AI 분석 결과</h4>
                    <p className="text-sm text-green-700 dark:text-green-300">
                      현재 기술적 지표들이 전반적으로 긍정적인 신호를 보이고 있습니다. 단기 조정 후 상승 추세 재개
                      가능성이 높습니다.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
