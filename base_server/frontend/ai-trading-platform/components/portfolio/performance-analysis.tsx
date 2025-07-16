"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts"

interface PerformanceAnalysisProps {
  detailed?: boolean
}

const performanceData = [
  { date: "2024-01", portfolio: 100, benchmark: 100, month: "1월" },
  { date: "2024-02", portfolio: 108.5, benchmark: 103.2, month: "2월" },
  { date: "2024-03", portfolio: 106.2, benchmark: 101.8, month: "3월" },
  { date: "2024-04", portfolio: 119.1, benchmark: 105.5, month: "4월" },
  { date: "2024-05", portfolio: 115.8, benchmark: 107.2, month: "5월" },
  { date: "2024-06", portfolio: 128.7, benchmark: 110.8, month: "6월" },
]

const riskMetrics = [
  { label: "총 수익률", value: "+28.7%", benchmark: "+10.8%", outperform: true },
  { label: "연환산 수익률", value: "+34.2%", benchmark: "+13.1%", outperform: true },
  { label: "변동성", value: "15.8%", benchmark: "12.3%", outperform: false },
  { label: "샤프 비율", value: "1.85", benchmark: "0.92", outperform: true },
  { label: "최대 낙폭", value: "-8.2%", benchmark: "-5.1%", outperform: false },
  { label: "베타", value: "1.12", benchmark: "1.00", outperform: false },
]

export function PerformanceAnalysis({ detailed = false }: PerformanceAnalysisProps) {
  return (
    <div className="space-y-6">
      {/* Performance Chart */}
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>포트폴리오 성과</span>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                포트폴리오
              </Badge>
              <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
                벤치마크
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <defs>
                  <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="benchmarkGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6b7280" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6b7280" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6b7280" }} />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#6b7280" }}
                  domain={["dataMin - 5", "dataMax + 5"]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(255, 255, 255, 0.95)",
                    border: "none",
                    borderRadius: "12px",
                    boxShadow: "0 10px 25px rgba(0, 0, 0, 0.1)",
                  }}
                  formatter={(value: number, name: string) => [
                    `${value.toFixed(1)}%`,
                    name === "portfolio" ? "포트폴리오" : "벤치마크",
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="portfolio"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#portfolioGradient)"
                  dot={false}
                />
                <Area
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#6b7280"
                  strokeWidth={2}
                  fill="url(#benchmarkGradient)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
          <CardHeader>
            <CardTitle>위험 지표</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {riskMetrics.map((metric) => (
                <div
                  key={metric.label}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-slate-700/50"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{metric.label}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">벤치마크: {metric.benchmark}</p>
                  </div>
                  <div className="text-right">
                    <p className={`font-bold text-lg ${metric.outperform ? "text-green-600" : "text-red-600"}`}>
                      {metric.value}
                    </p>
                    <Badge
                      variant="outline"
                      className={`text-xs ${
                        metric.outperform
                          ? "bg-green-50 text-green-700 border-green-200"
                          : "bg-red-50 text-red-700 border-red-200"
                      }`}
                    >
                      {metric.outperform ? "우수" : "주의"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
          <CardHeader>
            <CardTitle>월별 수익률</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {performanceData.slice(1).map((data, index) => {
                const monthlyReturn =
                  ((data.portfolio - performanceData[index].portfolio) / performanceData[index].portfolio) * 100
                const isPositive = monthlyReturn > 0

                return (
                  <div
                    key={data.month}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-slate-700/50"
                  >
                    <span className="font-medium text-gray-900 dark:text-white">{data.month}</span>
                    <div className="text-right">
                      <span className={`font-bold ${isPositive ? "text-green-600" : "text-red-600"}`}>
                        {isPositive ? "+" : ""}
                        {monthlyReturn.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {detailed && (
        <Card className="border-0 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 professional-shadow">
          <CardHeader>
            <CardTitle>상세 분석</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-2">87%</div>
                <p className="text-sm text-gray-600 dark:text-gray-400">승률</p>
                <p className="text-xs text-gray-500 mt-1">총 거래 중 수익 거래 비율</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">2.3</div>
                <p className="text-sm text-gray-600 dark:text-gray-400">손익비</p>
                <p className="text-xs text-gray-500 mt-1">평균 수익 / 평균 손실</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-2">156</div>
                <p className="text-sm text-gray-600 dark:text-gray-400">거래일수</p>
                <p className="text-xs text-gray-500 mt-1">활성 투자 기간</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
