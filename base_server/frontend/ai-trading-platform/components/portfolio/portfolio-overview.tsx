"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, DollarSign, Percent, PieChart } from "lucide-react"

const overviewData = [
  {
    title: "총 자산 가치",
    value: "₩125,847,230",
    change: "+₩13,847,230",
    changePercent: "+12.5%",
    isPositive: true,
    icon: DollarSign,
    gradient: "from-emerald-500 to-teal-600",
  },
  {
    title: "일일 손익",
    value: "+₩2,847,230",
    change: "오늘",
    changePercent: "+2.34%",
    isPositive: true,
    icon: TrendingUp,
    gradient: "from-blue-500 to-cyan-600",
  },
  {
    title: "총 수익률",
    value: "+18.7%",
    change: "전체 기간",
    changePercent: "목표 대비 +3.7%",
    isPositive: true,
    icon: Percent,
    gradient: "from-purple-500 to-pink-600",
  },
  {
    title: "포트폴리오 다양성",
    value: "8.2/10",
    change: "우수",
    changePercent: "리스크 분산",
    isPositive: true,
    icon: PieChart,
    gradient: "from-orange-500 to-red-600",
  },
]

export function PortfolioOverview() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      {overviewData.map((item, index) => {
        const Icon = item.icon
        return (
          <Card
            key={item.title}
            className="group relative overflow-hidden border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl hover-lift professional-shadow"
          >
            <div
              className={`absolute inset-0 bg-gradient-to-br ${item.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500`}
            />

            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-gradient-to-br ${item.gradient} text-white shadow-lg`}>
                  <Icon className="h-6 w-6" />
                </div>
                <Badge
                  variant="outline"
                  className={`${item.isPositive ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"}`}
                >
                  {item.isPositive ? (
                    <TrendingUp className="w-3 h-3 mr-1" />
                  ) : (
                    <TrendingDown className="w-3 h-3 mr-1" />
                  )}
                  {item.changePercent}
                </Badge>
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">{item.title}</h3>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{item.value}</div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{item.change}</p>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
