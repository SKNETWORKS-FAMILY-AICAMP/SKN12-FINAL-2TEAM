"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowUpRight, ArrowDownRight, Calendar, Filter } from "lucide-react"

const transactions = [
  {
    id: "1",
    type: "buy",
    symbol: "005930",
    name: "삼성전자",
    quantity: 50,
    price: 65000,
    totalAmount: 3250000,
    fee: 3250,
    date: "2024-01-15",
    time: "09:30:15",
    status: "completed",
  },
  {
    id: "2",
    type: "sell",
    symbol: "000660",
    name: "SK하이닉스",
    quantity: 20,
    price: 125000,
    totalAmount: 2500000,
    fee: 2500,
    date: "2024-01-14",
    time: "14:25:30",
    status: "completed",
  },
  {
    id: "3",
    type: "buy",
    symbol: "035420",
    name: "NAVER",
    quantity: 15,
    price: 180000,
    totalAmount: 2700000,
    fee: 2700,
    date: "2024-01-13",
    time: "11:45:22",
    status: "completed",
  },
  {
    id: "4",
    type: "buy",
    symbol: "035720",
    name: "카카오",
    quantity: 40,
    price: 52000,
    totalAmount: 2080000,
    fee: 2080,
    date: "2024-01-12",
    time: "16:20:10",
    status: "pending",
  },
]

export function TransactionHistory() {
  return (
    <div className="space-y-6">
      {/* Filter Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            기간 선택
          </Button>
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            필터
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">총 {transactions.length}건</Badge>
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            완료 {transactions.filter((t) => t.status === "completed").length}건
          </Badge>
        </div>
      </div>

      {/* Transaction List */}
      <div className="space-y-4">
        {transactions.map((transaction) => (
          <Card
            key={transaction.id}
            className="border-0 bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700 transition-all duration-300"
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div
                    className={`p-3 rounded-xl ${
                      transaction.type === "buy"
                        ? "bg-gradient-to-br from-blue-500 to-indigo-600"
                        : "bg-gradient-to-br from-red-500 to-pink-600"
                    } text-white`}
                  >
                    {transaction.type === "buy" ? (
                      <ArrowUpRight className="h-5 w-5" />
                    ) : (
                      <ArrowDownRight className="h-5 w-5" />
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white text-lg">{transaction.name}</h3>
                      <Badge variant={transaction.type === "buy" ? "default" : "destructive"} className="text-xs">
                        {transaction.type === "buy" ? "매수" : "매도"}
                      </Badge>
                      <Badge variant={transaction.status === "completed" ? "default" : "secondary"} className="text-xs">
                        {transaction.status === "completed" ? "완료" : "대기"}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {transaction.symbol} • {transaction.date} {transaction.time}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-8">
                  <div className="text-right">
                    <p className="text-sm text-gray-500 dark:text-gray-400">수량</p>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {transaction.quantity.toLocaleString()}주
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-sm text-gray-500 dark:text-gray-400">단가</p>
                    <p className="font-semibold text-gray-900 dark:text-white">₩{transaction.price.toLocaleString()}</p>
                  </div>

                  <div className="text-right">
                    <p className="text-sm text-gray-500 dark:text-gray-400">총 금액</p>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      ₩{transaction.totalAmount.toLocaleString()}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-sm text-gray-500 dark:text-gray-400">수수료</p>
                    <p className="font-semibold text-gray-900 dark:text-white">₩{transaction.fee.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Summary */}
      <Card className="border-0 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 professional-shadow">
        <CardHeader>
          <CardTitle>거래 요약</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {transactions.filter((t) => t.type === "buy").length}건
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">매수 거래</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {transactions.filter((t) => t.type === "sell").length}건
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">매도 거래</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ₩{transactions.reduce((sum, t) => sum + t.totalAmount, 0).toLocaleString()}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">총 거래금액</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                ₩{transactions.reduce((sum, t) => sum + t.fee, 0).toLocaleString()}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">총 수수료</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
