"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { Calculator, FileText, Download, Calendar } from "lucide-react"

interface TaxReportProps {
  period: string
}

const taxData = [
  { month: "1월", realized: 450000, unrealized: 320000 },
  { month: "2월", realized: 680000, unrealized: 420000 },
  { month: "3월", realized: -120000, unrealized: 580000 },
  { month: "4월", realized: 890000, unrealized: 340000 },
  { month: "5월", realized: 560000, unrealized: 720000 },
  { month: "6월", realized: 1200000, unrealized: 450000 },
]

const taxBreakdown = [
  { name: "단기 양도소득", value: 1800000, rate: 22, color: "#ef4444" },
  { name: "장기 양도소득", value: 2400000, rate: 15, color: "#f59e0b" },
  { name: "배당소득", value: 800000, rate: 14, color: "#10b981" },
  { name: "이자소득", value: 200000, rate: 14, color: "#3b82f6" },
]

export function TaxReport({ period }: TaxReportProps) {
  const totalTaxableIncome = taxBreakdown.reduce((sum, item) => sum + item.value, 0)
  const estimatedTax = taxBreakdown.reduce((sum, item) => sum + (item.value * item.rate) / 100, 0)

  return (
    <div className="space-y-6">
      {/* Tax Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">과세 대상 소득</p>
                <p className="text-2xl font-bold text-orange-900">₩{(totalTaxableIncome / 1000000).toFixed(1)}M</p>
                <p className="text-xs text-orange-600">{period} 누적</p>
              </div>
              <Calculator className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">예상 세금</p>
                <p className="text-2xl font-bold text-red-900">₩{(estimatedTax / 1000000).toFixed(1)}M</p>
                <p className="text-xs text-red-600">
                  평균 세율 {((estimatedTax / totalTaxableIncome) * 100).toFixed(1)}%
                </p>
              </div>
              <FileText className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">세후 수익</p>
                <p className="text-2xl font-bold text-green-900">
                  ₩{((totalTaxableIncome - estimatedTax) / 1000000).toFixed(1)}M
                </p>
                <p className="text-xs text-green-600">실제 수령액</p>
              </div>
              <Download className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">절세 효과</p>
                <p className="text-2xl font-bold text-blue-900">₩{((estimatedTax * 0.15) / 1000000).toFixed(1)}M</p>
                <p className="text-xs text-blue-600">최적화 전략 적용</p>
              </div>
              <Calendar className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Tax Analysis */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="w-5 h-5 text-orange-500" />
            월별 과세 소득 분석
          </CardTitle>
          <CardDescription>실현 손익 vs 미실현 손익 ({period} 기준)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={taxData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value: number) => [`₩${(value / 1000).toLocaleString()}K`, ""]} />
                <Bar dataKey="realized" fill="#ef4444" name="실현 손익" radius={[4, 4, 0, 0]} />
                <Bar dataKey="unrealized" fill="#6b7280" name="미실현 손익" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Tax Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>소득 유형별 세금</CardTitle>
            <CardDescription>과세 소득 구성 및 세율</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={taxBreakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {taxBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [`₩${(value / 1000000).toFixed(1)}M`, "소득"]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-1 gap-2 mt-4">
              {taxBreakdown.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                    <span className="text-sm font-medium">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold">₩{(item.value / 1000000).toFixed(1)}M</p>
                    <p className="text-xs text-gray-500">세율 {item.rate}%</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle>세금 최적화 전략</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200">
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">손익 실현 타이밍 조절</h4>
              <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">연말까지 손실 종목 매도로 세금 절약 가능</p>
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-600">예상 절세액</span>
                <span className="font-semibold text-blue-900 dark:text-blue-100">
                  ₩{((estimatedTax * 0.2) / 1000000).toFixed(1)}M
                </span>
              </div>
            </div>

            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200">
              <h4 className="font-medium text-green-900 dark:text-green-100 mb-2">장기 보유 전환</h4>
              <p className="text-sm text-green-700 dark:text-green-300 mb-3">1년 이상 보유 시 세율 혜택 적용</p>
              <div className="flex justify-between items-center">
                <span className="text-sm text-green-600">예상 절세액</span>
                <span className="font-semibold text-green-900 dark:text-green-100">
                  ₩{((estimatedTax * 0.1) / 1000000).toFixed(1)}M
                </span>
              </div>
            </div>

            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200">
              <h4 className="font-medium text-purple-900 dark:text-purple-100 mb-2">ISA 계좌 활용</h4>
              <p className="text-sm text-purple-700 dark:text-purple-300 mb-3">비과세 한도 내에서 투자 수익 최적화</p>
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-600">연간 한도</span>
                <span className="font-semibold text-purple-900 dark:text-purple-100">₩20M</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tax Calendar */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-purple-500" />
            세무 일정
          </CardTitle>
          <CardDescription>중요한 세무 신고 및 납부 일정</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { date: "2024-05-31", event: "종합소득세 신고", status: "완료", color: "green" },
              { date: "2024-08-31", event: "중간예납", status: "예정", color: "blue" },
              { date: "2024-12-31", event: "연말정산 준비", status: "예정", color: "orange" },
              { date: "2025-03-31", event: "양도소득세 신고", status: "예정", color: "red" },
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      item.color === "green"
                        ? "bg-green-500"
                        : item.color === "blue"
                          ? "bg-blue-500"
                          : item.color === "orange"
                            ? "bg-orange-500"
                            : "bg-red-500"
                    }`}
                  ></div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{item.event}</h4>
                    <p className="text-sm text-gray-500">{item.date}</p>
                  </div>
                </div>
                <Badge
                  className={`${
                    item.status === "완료"
                      ? "bg-green-100 text-green-800 border-green-200"
                      : "bg-blue-100 text-blue-800 border-blue-200"
                  } border`}
                >
                  {item.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
