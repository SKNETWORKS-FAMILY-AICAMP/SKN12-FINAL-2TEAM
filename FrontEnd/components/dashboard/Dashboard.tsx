"use client"

import { useState } from "react"
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
import { ArrowUpIcon, ArrowDownIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline"
import type { Stock, Portfolio, MarketAlert } from "../../types"

// Mock data - in real app, this would come from APIs
const mockStocks: Stock[] = [
  { symbol: "AAPL", name: "Apple Inc.", price: 175.43, change: 2.34, changePercent: 1.35, volume: 45234567 },
  { symbol: "GOOGL", name: "Alphabet Inc.", price: 2734.56, change: -15.23, changePercent: -0.55, volume: 1234567 },
  { symbol: "TSLA", name: "Tesla Inc.", price: 234.67, change: 8.45, changePercent: 3.74, volume: 23456789 },
  { symbol: "MSFT", name: "Microsoft Corp.", price: 334.12, change: 1.23, changePercent: 0.37, volume: 12345678 },
]

const mockPortfolio: Portfolio = {
  id: "1",
  stocks: [
    {
      symbol: "AAPL",
      name: "Apple Inc.",
      shares: 10,
      avgPrice: 170.0,
      currentPrice: 175.43,
      totalValue: 1754.3,
      return: 54.3,
      returnPercent: 3.19,
    },
    {
      symbol: "GOOGL",
      name: "Alphabet Inc.",
      shares: 2,
      avgPrice: 2800.0,
      currentPrice: 2734.56,
      totalValue: 5469.12,
      return: -130.88,
      returnPercent: -2.34,
    },
  ],
  totalValue: 7223.42,
  totalReturn: -76.58,
  totalReturnPercent: -1.05,
  cash: 2776.58,
}

const mockAlerts: MarketAlert[] = [
  {
    id: "1",
    type: "surge",
    title: "TSLA Surge Alert",
    message: "Tesla stock up 3.74% in the last hour",
    timestamp: new Date(),
    severity: "medium",
  },
  {
    id: "2",
    type: "news",
    title: "Market News",
    message: "Fed announces interest rate decision",
    timestamp: new Date(),
    severity: "high",
  },
  {
    id: "3",
    type: "target",
    title: "Target Reached",
    message: "Your AAPL position reached target price",
    timestamp: new Date(),
    severity: "low",
  },
]

const chartData = [
  { time: "09:30", value: 10000 },
  { time: "10:00", value: 10150 },
  { time: "10:30", value: 10080 },
  { time: "11:00", value: 10200 },
  { time: "11:30", value: 10350 },
  { time: "12:00", value: 10280 },
  { time: "12:30", value: 10400 },
  { time: "13:00", value: 10223 },
]

const COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]

export default function Dashboard() {
  const [stocks] = useState<Stock[]>(mockStocks)
  const [portfolio] = useState<Portfolio>(mockPortfolio)
  const [alerts] = useState<MarketAlert[]>(mockAlerts)

  const portfolioData = portfolio.stocks.map((stock, index) => ({
    name: stock.symbol,
    value: stock.totalValue,
    color: COLORS[index % COLORS.length],
  }))

  const handleCardClick = (cardType: string) => {
    console.log(`${cardType} 카드 클릭됨 - 상세 정보 표시`)
    // 실제로는 모달이나 상세 페이지로 이동
  }

  return (
    <div className="space-y-6 dashboard-content animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">대시보드</h1>
        <p className="text-gray-300">다시 오신 것을 환영합니다! 포트폴리오 현황을 확인하세요.</p>
      </div>

      {/* Portfolio Summary Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 portfolio-cards">
        <div
          className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 overflow-hidden shadow-xl rounded-xl hover:bg-gray-900/70 transition-all duration-300 hover:scale-105 cursor-pointer"
          onClick={() => handleCardClick("total-value")}
        >
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-white text-lg font-bold">$</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-300 truncate">총 자산</dt>
                  <dd className="text-xl font-bold text-white">${portfolio.totalValue.toLocaleString()}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div
          className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 overflow-hidden shadow-xl rounded-xl hover:bg-gray-900/70 transition-all duration-300 hover:scale-105 cursor-pointer"
          onClick={() => handleCardClick("total-return")}
        >
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg ${
                    portfolio.totalReturn >= 0
                      ? "bg-gradient-to-r from-green-500 to-green-600"
                      : "bg-gradient-to-r from-red-500 to-red-600"
                  }`}
                >
                  {portfolio.totalReturn >= 0 ? (
                    <ArrowUpIcon className="w-6 h-6 text-white" />
                  ) : (
                    <ArrowDownIcon className="w-6 h-6 text-white" />
                  )}
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-300 truncate">총 수익</dt>
                  <dd className={`text-xl font-bold ${portfolio.totalReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
                    ${portfolio.totalReturn.toFixed(2)} ({portfolio.totalReturnPercent.toFixed(2)}%)
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div
          className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 overflow-hidden shadow-xl rounded-xl hover:bg-gray-900/70 transition-all duration-300 hover:scale-105 cursor-pointer"
          onClick={() => handleCardClick("cash")}
        >
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-white text-lg font-bold">C</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-300 truncate">현금</dt>
                  <dd className="text-xl font-bold text-white">${portfolio.cash.toLocaleString()}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div
          className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 overflow-hidden shadow-xl rounded-xl hover:bg-gray-900/70 transition-all duration-300 hover:scale-105 cursor-pointer"
          onClick={() => handleCardClick("holdings")}
        >
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-white text-lg font-bold">#</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-300 truncate">보유 종목</dt>
                  <dd className="text-xl font-bold text-white">{portfolio.stocks.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 performance-chart">
        {/* Portfolio Performance Chart */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 shadow-xl rounded-xl p-6 hover:bg-gray-900/70 transition-all duration-300">
          <h3 className="text-xl font-bold text-white mb-4">포트폴리오 성과</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1F2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                    color: "#ffffff",
                  }}
                />
                <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Portfolio Allocation */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 shadow-xl rounded-xl p-6 hover:bg-gray-900/70 transition-all duration-300">
          <h3 className="text-xl font-bold text-white mb-4">포트폴리오 배분</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={portfolioData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {portfolioData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [`$${value.toLocaleString()}`, "Value"]}
                  contentStyle={{
                    backgroundColor: "#1F2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                    color: "#ffffff",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Market Alerts and Top Stocks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 market-section">
        {/* Market Alerts */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 shadow-xl rounded-xl hover:bg-gray-900/70 transition-all duration-300">
          <div className="px-6 py-4 border-b border-gray-800/50">
            <h3 className="text-xl font-bold text-white">시장 알림</h3>
          </div>
          <div className="divide-y divide-gray-800/50">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="px-6 py-4 hover:bg-gray-800/30 transition-colors duration-300 cursor-pointer"
                onClick={() => console.log(`알림 클릭: ${alert.title}`)}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <ExclamationTriangleIcon
                      className={`h-5 w-5 ${
                        alert.severity === "high"
                          ? "text-red-400"
                          : alert.severity === "medium"
                            ? "text-yellow-400"
                            : "text-blue-400"
                      }`}
                    />
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-white">{alert.title}</p>
                    <p className="text-sm text-gray-300">{alert.message}</p>
                    <p className="text-xs text-gray-400 mt-1">{alert.timestamp.toLocaleTimeString()}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Stocks */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 shadow-xl rounded-xl hover:bg-gray-900/70 transition-all duration-300">
          <div className="px-6 py-4 border-b border-gray-800/50">
            <h3 className="text-xl font-bold text-white">주요 종목</h3>
          </div>
          <div className="divide-y divide-gray-800/50">
            {stocks.map((stock) => (
              <div
                key={stock.symbol}
                className="px-6 py-4 hover:bg-gray-800/30 transition-colors duration-300 cursor-pointer"
                onClick={() => console.log(`종목 클릭: ${stock.symbol}`)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">{stock.symbol}</p>
                    <p className="text-sm text-gray-300">{stock.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-white">${stock.price.toFixed(2)}</p>
                    <p className={`text-sm ${stock.change >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {stock.change >= 0 ? "+" : ""}
                      {stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
