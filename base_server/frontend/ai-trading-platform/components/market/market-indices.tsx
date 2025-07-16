"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Activity } from "lucide-react"

const indices = [
  {
    name: "KOSPI",
    value: 2485.67,
    change: 12.34,
    changePercent: 0.5,
    volume: "₩8.2조",
    status: "up",
  },
  {
    name: "KOSDAQ",
    value: 845.23,
    change: -5.67,
    changePercent: -0.67,
    volume: "₩3.1조",
    status: "down",
  },
  {
    name: "S&P 500",
    value: 4567.89,
    change: 23.45,
    changePercent: 0.52,
    volume: "$142B",
    status: "up",
  },
  {
    name: "NASDAQ",
    value: 14234.56,
    change: 45.67,
    changePercent: 0.32,
    volume: "$89B",
    status: "up",
  },
  {
    name: "DOW",
    value: 34567.12,
    change: -12.34,
    changePercent: -0.04,
    volume: "$98B",
    status: "down",
  },
  {
    name: "NIKKEI",
    value: 28456.78,
    change: 156.23,
    changePercent: 0.55,
    volume: "¥2.1조",
    status: "up",
  },
]

export function MarketIndices() {
  return (
    <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-3 text-xl">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
              <Activity className="h-5 w-5" />
            </div>
            주요 지수
          </CardTitle>
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
            실시간
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {indices.map((index) => (
            <div
              key={index.name}
              className="p-4 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-700 dark:to-slate-800 hover:from-blue-50 hover:to-indigo-50 dark:hover:from-slate-600 dark:hover:to-slate-700 transition-all duration-300 border border-gray-200 dark:border-gray-600 hover:shadow-md"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 dark:text-white text-lg">{index.name}</h3>
                <div className="flex items-center gap-1">
                  {index.status === "up" ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500" />
                  )}
                  <Badge
                    variant={index.status === "up" ? "default" : "destructive"}
                    className={`text-xs ${
                      index.status === "up" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                    }`}
                  >
                    {index.status === "up" ? "상승" : "하락"}
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{index.value.toLocaleString()}</div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${index.change > 0 ? "text-green-600" : "text-red-600"}`}>
                      {index.change > 0 ? "+" : ""}
                      {index.change.toFixed(2)}
                    </span>
                    <span
                      className={`text-sm font-medium ${index.changePercent > 0 ? "text-green-600" : "text-red-600"}`}
                    >
                      ({index.changePercent > 0 ? "+" : ""}
                      {index.changePercent.toFixed(2)}%)
                    </span>
                  </div>
                </div>

                <div className="text-xs text-gray-500 dark:text-gray-400">거래량: {index.volume}</div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
