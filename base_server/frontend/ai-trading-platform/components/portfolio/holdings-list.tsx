"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendingUp, TrendingDown, MoreHorizontal } from "lucide-react"

const holdings = [
  {
    symbol: "005930",
    name: "삼성전자",
    quantity: 50,
    avgPrice: 65000,
    currentPrice: 68500,
    value: 3425000,
    pnl: 175000,
    pnlPercent: 5.38,
    weight: 28.5,
    sector: "기술",
  },
  {
    symbol: "000660",
    name: "SK하이닉스",
    quantity: 30,
    avgPrice: 120000,
    currentPrice: 115000,
    value: 3450000,
    pnl: -150000,
    pnlPercent: -4.17,
    weight: 28.7,
    sector: "반도체",
  },
  {
    symbol: "035420",
    name: "NAVER",
    quantity: 20,
    avgPrice: 180000,
    currentPrice: 185000,
    value: 3700000,
    pnl: 100000,
    pnlPercent: 2.78,
    weight: 30.8,
    sector: "인터넷",
  },
  {
    symbol: "035720",
    name: "카카오",
    quantity: 40,
    avgPrice: 52000,
    currentPrice: 48500,
    value: 1940000,
    pnl: -140000,
    pnlPercent: -6.73,
    weight: 16.1,
    sector: "인터넷",
  },
]

export function HoldingsList() {
  return (
    <div className="space-y-4">
      {holdings.map((holding) => (
        <Card
          key={holding.symbol}
          className="border-0 bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700 transition-all duration-300 hover-lift"
        >
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold">
                  {holding.name.charAt(0)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white text-lg">{holding.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm text-gray-500 dark:text-gray-400">{holding.symbol}</span>
                    <Badge variant="outline" className="text-xs">
                      {holding.sector}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">보유량</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{holding.quantity}주</p>
                </div>

                <div className="text-right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">현재가</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    ₩{holding.currentPrice.toLocaleString()}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">평가금액</p>
                  <p className="font-semibold text-gray-900 dark:text-white">₩{holding.value.toLocaleString()}</p>
                </div>

                <div className="text-right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">손익</p>
                  <div className="flex items-center gap-1">
                    {holding.pnl > 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    <span className={`font-semibold ${holding.pnl > 0 ? "text-green-600" : "text-red-600"}`}>
                      {holding.pnl > 0 ? "+" : ""}₩{holding.pnl.toLocaleString()}
                    </span>
                  </div>
                  <p className={`text-sm ${holding.pnl > 0 ? "text-green-600" : "text-red-600"}`}>
                    ({holding.pnl > 0 ? "+" : ""}
                    {holding.pnlPercent.toFixed(2)}%)
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">비중</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{holding.weight}%</p>
                </div>

                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
