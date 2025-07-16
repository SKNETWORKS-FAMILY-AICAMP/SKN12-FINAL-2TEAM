"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"
import { TrendingUp, Calendar, BarChart3, Download, TrendingDown } from "lucide-react"

const backtestData = [
  { date: "2024-01", portfolio: 100000, benchmark: 100000 },
  { date: "2024-02", portfolio: 103500, benchmark: 101200 },
  { date: "2024-03", portfolio: 108200, benchmark: 102800 },
  { date: "2024-04", portfolio: 105800, benchmark: 104100 },
  { date: "2024-05", portfolio: 112400, benchmark: 106500 },
  { date: "2024-06", portfolio: 118900, benchmark: 108200 },
  { date: "2024-07", portfolio: 124700, benchmark: 110800 },
]

const monthlyReturns = [
  { month: "1월", returns: 3.5, benchmark: 1.2 },
  { month: "2월", returns: 4.5, benchmark: 1.6 },
  { month: "3월", returns: -2.2, benchmark: 1.3 },
  { month: "4월", returns: 6.2, benchmark: 2.4 },
  { month: "5월", returns: 5.8, benchmark: 1.7 },
  { month: "6월", returns: 4.9, benchmark: 2.3 },
]

export function BacktestResults() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">백테스트 결과</h2>
        <div className="flex gap-3">
          <Button variant="outline">
            <Calendar className="w-4 h-4 mr-2" />
            기간 설정
          </Button>
          <Button className="bg-blue-500 hover:bg-blue-600 text-white">
            <Download className="w-4 h-4 mr-2" />
            리포트 다운로드
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
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
                <p className="text-sm font-medium text-blue-600">샤프 비율</p>
                <p className="text-2xl font-bold text-blue-900">1.84</p>
                <p className="text-xs text-blue-600">우수한 위험조정수익</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">최대 낙폭</p>
                <p className="text-2xl font-bold text-purple-900">-8.3%</p>
                <p className="text-xs text-purple-600">양호한 리스크 관리</p>
              </div>
              <TrendingDown className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">승률</p>
                <p className="text-2xl font-bold text-orange-900">68.4%</p>
                <p className="text-xs text-orange-600">234회 중 160회 수익</p>
              </div>
              <BarChart3 className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Chart */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            누적 수익률 비교
          </CardTitle>
          <CardDescription>포트폴리오 vs 벤치마크 (KOSPI) 성과 비교</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={backtestData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => [`₩${value.toLocaleString()}`, ""]}
                  labelFormatter={(label) => `기간: ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="portfolio"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  name="포트폴리오"
                  dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#6b7280"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="벤치마크"
                  dot={{ fill: "#6b7280", strokeWidth: 2, r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Monthly Returns */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-green-500" />
            월별 수익률
          </CardTitle>
          <CardDescription>월별 포트폴리오 수익률 vs 벤치마크</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyReturns}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value: number) => [`${value}%`, ""]} />
                <Bar dataKey="returns" fill="#3b82f6" name="포트폴리오" radius={[4, 4, 0, 0]} />
                <Bar dataKey="benchmark" fill="#6b7280" name="벤치마크" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>리스크 지표</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">변동성 (연환산)</span>
              <span className="font-semibold">12.4%</span>
            </div>
            <Progress value={62} className="h-2" />

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">베타</span>
              <span className="font-semibold">0.87</span>
            </div>
            <Progress value={87} className="h-2" />

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">알파</span>
              <span className="font-semibold">+5.2%</span>
            </div>
            <Progress value={78} className="h-2" />
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>거래 통계</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">총 거래 횟수</span>
              <span className="font-semibold">234회</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">평균 보유 기간</span>
              <span className="font-semibold">3.2일</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">최대 수익 거래</span>
              <span className="font-semibold text-green-600">+8.7%</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">최대 손실 거래</span>
              <span className="font-semibold text-red-600">-4.2%</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
