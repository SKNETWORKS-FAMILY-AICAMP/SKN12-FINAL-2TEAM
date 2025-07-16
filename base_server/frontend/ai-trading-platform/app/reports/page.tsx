"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { PerformanceReport } from "@/components/reports/performance-report"
import { RiskReport } from "@/components/reports/risk-report"
import { TaxReport } from "@/components/reports/tax-report"
import { CustomReport } from "@/components/reports/custom-report"
import { Download, Calendar, TrendingUp, Shield, Calculator, BarChart3 } from "lucide-react"

export default function ReportsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState("1M")

  const periods = [
    { label: "1주", value: "1W" },
    { label: "1개월", value: "1M" },
    { label: "3개월", value: "3M" },
    { label: "6개월", value: "6M" },
    { label: "1년", value: "1Y" },
    { label: "전체", value: "ALL" },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
            투자 리포트
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">포괄적인 투자 성과 분석 및 세무 리포트</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <div className="flex bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-1">
              {periods.map((period) => (
                <button
                  key={period.value}
                  onClick={() => setSelectedPeriod(period.value)}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-all duration-200 ${
                    selectedPeriod === period.value
                      ? "bg-blue-500 text-white shadow-sm"
                      : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  }`}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
          <Button className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 font-medium transition-all duration-300">
            <Download className="w-4 h-4 mr-2" />
            PDF 다운로드
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">총 수익률</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100">+24.7%</p>
                <p className="text-xs text-green-600 dark:text-green-400">지난달 대비 +3.2%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-400">샤프 비율</p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">1.84</p>
                <p className="text-xs text-blue-600 dark:text-blue-400">우수한 위험조정수익</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600 dark:text-purple-400">최대 낙폭</p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">-8.3%</p>
                <p className="text-xs text-purple-600 dark:text-purple-400">양호한 리스크 관리</p>
              </div>
              <Shield className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-700 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600 dark:text-orange-400">예상 세금</p>
                <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">₩2.4M</p>
                <p className="text-xs text-orange-600 dark:text-orange-400">올해 과세 대상</p>
              </div>
              <Calculator className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="performance" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
          <TabsTrigger
            value="performance"
            className="data-[state=active]:bg-green-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            성과 리포트
          </TabsTrigger>
          <TabsTrigger
            value="risk"
            className="data-[state=active]:bg-green-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            리스크 분석
          </TabsTrigger>
          <TabsTrigger
            value="tax"
            className="data-[state=active]:bg-green-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            세무 리포트
          </TabsTrigger>
          <TabsTrigger
            value="custom"
            className="data-[state=active]:bg-green-500 data-[state=active]:text-white rounded-lg transition-all duration-300"
          >
            맞춤 리포트
          </TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-6">
          <PerformanceReport period={selectedPeriod} />
        </TabsContent>

        <TabsContent value="risk" className="space-y-6">
          <RiskReport period={selectedPeriod} />
        </TabsContent>

        <TabsContent value="tax" className="space-y-6">
          <TaxReport period={selectedPeriod} />
        </TabsContent>

        <TabsContent value="custom" className="space-y-6">
          <CustomReport />
        </TabsContent>
      </Tabs>
    </div>
  )
}
