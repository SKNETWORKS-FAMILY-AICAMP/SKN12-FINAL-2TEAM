"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { TrendingUp, Target, Award, Calendar } from "lucide-react"

interface PerformanceReportProps {
  period: string
}

const performanceData = [
  { date: "2024-01", portfolio: 100000, benchmark: 100000, alpha: 0 },
  { date: "2024-02", portfolio: 103500, benchmark: 101200, alpha: 2.3 },
  { date: "2024-03", portfolio: 108200, benchmark: 102800, alpha: 5.4 },
  { date: "2024-04", portfolio: 105800, benchmark: 104100, alpha: 1.7 },
  { date: "2024-05", portfolio: 112400, benchmark: 106500, alpha: 5.9 },
  { date: "2024-06", portfolio: 118900, benchmark: 108200, alpha: 10.7 },
  { date: "2024-07", portfolio: 124700, benchmark: 110800, alpha: 13.9 },
]

const sectorAllocation = [
  { name: "기술", value: 35, color: "#3b82f6" },
  { name: "금융", value: 20, color: "#10b981" },
  { name: "헬스케어", value: 15, color: "#f59e0b" },
  { name: "소비재", value: 12, color: "#ef4444" },
  { name: "에너지", value: 10, color: "#8b5cf6" },
  { name: "기타", value: 8, color: "#6b7280" },
]

export function PerformanceReport({ period }: PerformanceReportProps) {
  return (
    <div className="space-y-6">
      {/* Performance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">총 수익률</p>
                <p className="text-2xl font-bold text-green-900">+24.7%</p>
                <p className="text-xs text-green-600">vs 벤치마크 +10.8%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">연환산 수익률</p>
                <p className="text-2xl font-bold text-blue-900">+42.3%</p>
                <p className="text-xs text-blue-600">목표 대비 +12.3%</p>
              </div>
              <Target className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">샤프 비율</p>
                <p className="text-2xl font-bold text-purple-900">1.84</p>
                <p className="text-xs text-purple-600">우수한 위험조정수익</p>
              </div>
              <Award className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">알파</p>
                <p className="text-2xl font-bold text-orange-900">+13.9%</p>
                <p className="text-xs text-orange-600">시장 초과 수익</p>
              </div>
              <Calendar className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Chart */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            누적 성과 분석
          </CardTitle>
          <CardDescription>포트폴리오 vs 벤치마크 성과 비교 ({period} 기준)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `₩${value.toLocaleString()}`,
                    name === "portfolio" ? "포트폴리오" : name === "benchmark" ? "벤치마크" : "알파",
                  ]}
                  labelFormatter={(label) => `기간: ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="portfolio"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  name="portfolio"
                  dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#6b7280"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="benchmark"
                  dot={{ fill: "#6b7280", strokeWidth: 2, r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Metrics & Sector Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>상세 성과 지표</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">변동성 (연환산)</span>
              <span className="font-semibold">12.4%</span>
            </div>
            <Progress value={62} className="h-2" />

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">최대 낙폭</span>
              <span className="font-semibold text-red-600">-8.3%</span>
            </div>
            <Progress value={17} className="h-2" />

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">베타</span>
              <span className="font-semibold">0.87</span>
            </div>
            <Progress value={87} className="h-2" />

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">정보 비율</span>
              <span className="font-semibold">1.23</span>
            </div>
            <Progress value={82} className="h-2" />

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">승률</span>
              <span className="font-semibold text-green-600">68.4%</span>
            </div>
            <Progress value={68} className="h-2" />
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>섹터별 배분</CardTitle>
            <CardDescription>현재 포트폴리오 섹터 구성</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sectorAllocation}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {sectorAllocation.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value}%`, "비중"]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {sectorAllocation.map((sector, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: sector.color }}></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {sector.name} {sector.value}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Attribution */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle>성과 기여도 분석</CardTitle>
          <CardDescription>각 섹터별 포트폴리오 성과 기여도</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { sector: "기술", contribution: 8.7, allocation: 35 },
              { sector: "금융", contribution: 4.2, allocation: 20 },
              { sector: "헬스케어", contribution: 3.1, allocation: 15 },
              { sector: "소비재", contribution: 2.8, allocation: 12 },
              { sector: "에너지", contribution: 5.9, allocation: 10 },
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                    <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">{item.allocation}%</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{item.sector}</h4>
                    <p className="text-sm text-gray-500">포트폴리오 비중 {item.allocation}%</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-green-600">+{item.contribution}%</p>
                  <p className="text-sm text-gray-500">성과 기여도</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
