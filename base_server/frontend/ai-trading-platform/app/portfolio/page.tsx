"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PortfolioOverview } from "@/components/portfolio/portfolio-overview"
import { HoldingsList } from "@/components/portfolio/holdings-list"
import { Wallet, TrendingUp, History, BarChart3, Plus } from "lucide-react"

export default function PortfolioPage() {
  const [activeTab, setActiveTab] = useState("overview")

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">포트폴리오</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">투자 현황과 성과를 한눈에 확인하세요</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="bg-white/80 dark:bg-slate-800/80">
            <History className="h-4 w-4 mr-2" />
            거래 내역
          </Button>
          <Button className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700">
            <Plus className="h-4 w-4 mr-2" />새 거래
          </Button>
        </div>
      </div>

      {/* Portfolio Overview Cards */}
      <PortfolioOverview />

      {/* Main Content Tabs */}
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white">
              <Wallet className="h-5 w-5" />
            </div>
            포트폴리오 상세
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-4 bg-gray-100 dark:bg-slate-700">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                개요
              </TabsTrigger>
              <TabsTrigger value="holdings" className="flex items-center gap-2">
                <Wallet className="h-4 w-4" />
                보유 종목
              </TabsTrigger>
              <TabsTrigger value="transactions" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                거래 내역
              </TabsTrigger>
              <TabsTrigger value="performance" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                성과 분석
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="border-0 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 professional-shadow">
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">월별 수익률</h3>
                    <div className="space-y-3">
                      {[
                        { month: "1월", return: 8.5, positive: true },
                        { month: "2월", return: -2.1, positive: false },
                        { month: "3월", return: 12.3, positive: true },
                        { month: "4월", return: 5.7, positive: true },
                      ].map((item) => (
                        <div key={item.month} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">{item.month}</span>
                          <span className={`font-semibold ${item.positive ? "text-green-600" : "text-red-600"}`}>
                            {item.positive ? "+" : ""}
                            {item.return}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 professional-shadow">
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">섹터별 분산</h3>
                    <div className="space-y-3">
                      {[
                        { sector: "기술", percentage: 45, color: "bg-blue-500" },
                        { sector: "금융", percentage: 25, color: "bg-green-500" },
                        { sector: "헬스케어", percentage: 20, color: "bg-purple-500" },
                        { sector: "기타", percentage: 10, color: "bg-gray-500" },
                      ].map((item) => (
                        <div key={item.sector} className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600 dark:text-gray-400">{item.sector}</span>
                            <span className="font-semibold text-gray-900 dark:text-white">{item.percentage}%</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className={`${item.color} h-2 rounded-full transition-all duration-500`}
                              style={{ width: `${item.percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="holdings" className="space-y-6">
              <HoldingsList />
            </TabsContent>

            <TabsContent value="transactions" className="space-y-6">
              <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
                <CardHeader>
                  <CardTitle>최근 거래 내역</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      {
                        type: "매수",
                        symbol: "삼성전자",
                        quantity: 10,
                        price: 68500,
                        date: "2024-01-15",
                        status: "완료",
                      },
                      {
                        type: "매도",
                        symbol: "SK하이닉스",
                        quantity: 5,
                        price: 115000,
                        date: "2024-01-14",
                        status: "완료",
                      },
                      {
                        type: "매수",
                        symbol: "NAVER",
                        quantity: 3,
                        price: 185000,
                        date: "2024-01-13",
                        status: "완료",
                      },
                    ].map((transaction, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-slate-700/50"
                      >
                        <div className="flex items-center gap-4">
                          <div
                            className={`px-3 py-1 rounded-full text-xs font-medium ${
                              transaction.type === "매수" ? "bg-blue-100 text-blue-700" : "bg-red-100 text-red-700"
                            }`}
                          >
                            {transaction.type}
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 dark:text-white">{transaction.symbol}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {transaction.quantity}주 × ₩{transaction.price.toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-gray-900 dark:text-white">
                            ₩{(transaction.quantity * transaction.price).toLocaleString()}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">{transaction.date}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="performance" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
                  <CardHeader>
                    <CardTitle>성과 지표</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {[
                        { label: "총 수익률", value: "+18.7%", positive: true },
                        { label: "연환산 수익률", value: "+24.3%", positive: true },
                        { label: "최대 낙폭", value: "-8.2%", positive: false },
                        { label: "샤프 비율", value: "1.45", positive: true },
                        { label: "변동성", value: "12.8%", positive: null },
                      ].map((metric) => (
                        <div key={metric.label} className="flex items-center justify-between">
                          <span className="text-gray-600 dark:text-gray-400">{metric.label}</span>
                          <span
                            className={`font-semibold ${
                              metric.positive === true
                                ? "text-green-600"
                                : metric.positive === false
                                  ? "text-red-600"
                                  : "text-gray-900 dark:text-white"
                            }`}
                          >
                            {metric.value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
                  <CardHeader>
                    <CardTitle>리스크 분석</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600 dark:text-gray-400">포트폴리오 리스크</span>
                          <span className="text-sm font-medium text-orange-600">중간</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div className="bg-orange-500 h-2 rounded-full w-3/5" />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600 dark:text-gray-400">다양성 점수</span>
                          <span className="text-sm font-medium text-green-600">높음</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full w-4/5" />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600 dark:text-gray-400">베타 계수</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">1.12</span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">시장 대비 12% 높은 변동성</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
