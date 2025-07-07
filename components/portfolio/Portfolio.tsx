"use client"

import { useState } from "react"
import { PlusIcon, ArrowUpIcon, ChartBarIcon, EyeIcon, TrashIcon } from "@heroicons/react/24/outline"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

const mockPortfolio = {
  id: "1",
  stocks: [
    {
      symbol: "AAPL",
      name: "애플",
      shares: 10,
      avgPrice: 170.0,
      currentPrice: 175.43,
      totalValue: 1754.3,
      return: 54.3,
      returnPercent: 3.19,
    },
    {
      symbol: "GOOGL",
      name: "알파벳",
      shares: 2,
      avgPrice: 2800.0,
      currentPrice: 2734.56,
      totalValue: 5469.12,
      return: -130.88,
      returnPercent: -2.34,
    },
    {
      symbol: "TSLA",
      name: "테슬라",
      shares: 5,
      avgPrice: 220.0,
      currentPrice: 234.67,
      totalValue: 1173.35,
      return: 73.35,
      returnPercent: 6.67,
    },
    {
      symbol: "MSFT",
      name: "마이크로소프트",
      shares: 8,
      avgPrice: 320.0,
      currentPrice: 334.12,
      totalValue: 2672.96,
      return: 112.96,
      returnPercent: 4.41,
    },
  ],
  totalValue: 11069.73,
  totalReturn: 109.73,
  totalReturnPercent: 1.0,
  cash: 3930.27,
}

const performanceData = [
  { date: "2024-01", value: 10000 },
  { date: "2024-02", value: 10500 },
  { date: "2024-03", value: 10200 },
  { date: "2024-04", value: 10800 },
  { date: "2024-05", value: 11200 },
  { date: "2024-06", value: 11070 },
]

export default function PortfolioComponent() {
  const [portfolio] = useState(mockPortfolio)
  const [selectedStock, setSelectedStock] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [hoveredCard, setHoveredCard] = useState(null)

  const handleAddPosition = () => {
    setShowAddModal(true)
  }

  const handleCardClick = (cardType: string) => {
    console.log(`${cardType} 카드 클릭됨`)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">포트폴리오</h1>
          <p className="text-gray-300">투자를 관리하고 성과를 추적하세요</p>
        </div>
        <Button
          onClick={handleAddPosition}
          className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-6 py-3 rounded-xl shadow-lg transform transition hover:scale-105 hover:shadow-xl duration-300 flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span className="font-semibold">포지션 추가</span>
        </Button>
      </div>

      {/* Portfolio Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Portfolio Value */}
        <Card
          className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/30 shadow-xl hover:shadow-2xl hover:bg-gray-800/50 transform hover:scale-105 transition-all duration-300 cursor-pointer"
          onClick={() => handleCardClick("portfolio-value")}
          onMouseEnter={() => setHoveredCard("portfolio")}
          onMouseLeave={() => setHoveredCard(null)}
        >
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                <ChartBarIcon className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-400 mb-1">총 포트폴리오 가치</p>
                <p className="text-2xl font-bold text-white">₩{(portfolio.totalValue * 1300).toLocaleString()}</p>
                {hoveredCard === "portfolio" && (
                  <p className="text-xs text-blue-400 mt-1 animate-fade-in">클릭하여 상세 보기</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Return */}
        <Card
          className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/30 shadow-xl hover:shadow-2xl hover:bg-gray-800/50 transform hover:scale-105 transition-all duration-300 cursor-pointer"
          onClick={() => handleCardClick("total-return")}
          onMouseEnter={() => setHoveredCard("return")}
          onMouseLeave={() => setHoveredCard(null)}
        >
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
                <ArrowUpIcon className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-400 mb-1">총 수익</p>
                <p className="text-2xl font-bold text-green-400">₩{(portfolio.totalReturn * 1300).toLocaleString()}</p>
                <p className="text-sm text-green-400 font-medium">{portfolio.totalReturnPercent.toFixed(2)}%</p>
                {hoveredCard === "return" && (
                  <p className="text-xs text-green-400 mt-1 animate-fade-in">수익률 분석 보기</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Available Cash */}
        <Card
          className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/30 shadow-xl hover:shadow-2xl hover:bg-gray-800/50 transform hover:scale-105 transition-all duration-300 cursor-pointer"
          onClick={() => handleCardClick("available-cash")}
          onMouseEnter={() => setHoveredCard("cash")}
          onMouseLeave={() => setHoveredCard(null)}
        >
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white text-xl font-bold">₩</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-400 mb-1">보유 현금</p>
                <p className="text-2xl font-bold text-white">₩{(portfolio.cash * 1300).toLocaleString()}</p>
                {hoveredCard === "cash" && (
                  <p className="text-xs text-yellow-400 mt-1 animate-fade-in">투자 가능 금액</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Chart */}
      <Card className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/30 shadow-xl hover:shadow-2xl hover:bg-gray-800/50 transition-all duration-300">
        <CardContent className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-white">포트폴리오 성과 (6개월)</h3>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                className="text-gray-400 border-gray-600/50 hover:bg-gray-700/50 hover:text-white bg-transparent"
              >
                1개월
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-gray-400 border-gray-600/50 hover:bg-gray-700/50 hover:text-white bg-transparent"
              >
                3개월
              </Button>
              <Button
                size="sm"
                className="bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700"
              >
                6개월
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-gray-400 border-gray-600/50 hover:bg-gray-700/50 hover:text-white bg-transparent"
              >
                1년
              </Button>
            </div>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} domain={[0, 12000]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1F2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    color: "#ffffff",
                  }}
                  formatter={(value: number) => [`₩${(value * 1300).toLocaleString()}`, "포트폴리오 가치"]}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ fill: "#3b82f6", strokeWidth: 2, r: 6 }}
                  activeDot={{ r: 8, stroke: "#3b82f6", strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Holdings Table */}
      <Card className="bg-gray-800/30 backdrop-blur-sm border border-gray-700/30 shadow-xl hover:shadow-2xl hover:bg-gray-800/50 transition-all duration-300">
        <CardContent className="p-0">
          <div className="px-6 py-4 border-b border-gray-700/30">
            <h3 className="text-xl font-bold text-white">보유 종목</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    종목
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    보유량
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    평균단가
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    현재가
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    총 가치
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    수익률
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    액션
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {portfolio.stocks.map((stock) => (
                  <tr
                    key={stock.symbol}
                    className="hover:bg-gray-700/30 transition-colors duration-200 cursor-pointer"
                    onClick={() => setSelectedStock(stock)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mr-3">
                          <span className="text-white font-bold text-sm">{stock.symbol.charAt(0)}</span>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-white">{stock.symbol}</div>
                          <div className="text-sm text-gray-400">{stock.name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">{stock.shares}주</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      ₩{(stock.avgPrice * 1300).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">
                      ₩{(stock.currentPrice * 1300).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-bold">
                      ₩{(stock.totalValue * 1300).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-bold ${stock.return >= 0 ? "text-green-400" : "text-red-400"}`}>
                        ₩{(stock.return * 1300).toLocaleString()}
                      </div>
                      <div className={`text-xs ${stock.return >= 0 ? "text-green-400" : "text-red-400"}`}>
                        {stock.returnPercent.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedStock(stock)
                          }}
                          className="text-blue-400 border-blue-500/30 hover:bg-blue-500/20 bg-transparent"
                        >
                          <EyeIcon className="w-4 h-4 mr-1" />
                          보기
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation()
                            console.log(`${stock.symbol} 매도`)
                          }}
                          className="text-red-400 border-red-500/30 hover:bg-red-500/20 bg-transparent"
                        >
                          <TrashIcon className="w-4 h-4 mr-1" />
                          매도
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Add Position Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4 bg-gray-800/95 backdrop-blur-sm border border-gray-700/50 shadow-2xl">
            <CardContent className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-white">새 포지션 추가</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddModal(false)}
                  className="text-gray-400 hover:text-white hover:bg-gray-700/50"
                >
                  ✕
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">종목 심볼</label>
                  <input
                    type="text"
                    placeholder="예: AAPL"
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">수량</label>
                  <input
                    type="number"
                    placeholder="예: 10"
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">매수가</label>
                  <input
                    type="number"
                    placeholder="예: 150,000"
                    className="w-full px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 bg-transparent border-gray-600/50 text-gray-400 hover:bg-gray-700/50 hover:text-white"
                >
                  취소
                </Button>
                <Button
                  onClick={() => {
                    console.log("새 포지션 추가")
                    setShowAddModal(false)
                  }}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                >
                  추가
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stock Detail Modal */}
      {selectedStock && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="w-full max-w-lg mx-4 bg-gray-800/95 backdrop-blur-sm border border-gray-700/50 shadow-2xl">
            <CardContent className="p-6">
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold">{selectedStock.symbol.charAt(0)}</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">{selectedStock.symbol}</h3>
                    <p className="text-gray-400">{selectedStock.name}</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedStock(null)}
                  className="text-gray-400 hover:text-white hover:bg-gray-700/50"
                >
                  ✕
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600/30">
                  <p className="text-sm text-gray-400">보유량</p>
                  <p className="text-lg font-bold text-white">{selectedStock.shares}주</p>
                </div>
                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600/30">
                  <p className="text-sm text-gray-400">평균단가</p>
                  <p className="text-lg font-bold text-white">₩{(selectedStock.avgPrice * 1300).toLocaleString()}</p>
                </div>
                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600/30">
                  <p className="text-sm text-gray-400">현재가</p>
                  <p className="text-lg font-bold text-white">
                    ₩{(selectedStock.currentPrice * 1300).toLocaleString()}
                  </p>
                </div>
                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600/30">
                  <p className="text-sm text-gray-400">총 가치</p>
                  <p className="text-lg font-bold text-white">₩{(selectedStock.totalValue * 1300).toLocaleString()}</p>
                </div>
              </div>

              <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 p-4 rounded-lg mb-6 border border-green-500/30">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">총 수익</span>
                  <div className="text-right">
                    <span
                      className={`text-lg font-bold ${selectedStock.return >= 0 ? "text-green-400" : "text-red-400"}`}
                    >
                      ₩{(selectedStock.return * 1300).toLocaleString()}
                    </span>
                    <span className={`text-sm ml-2 ${selectedStock.return >= 0 ? "text-green-400" : "text-red-400"}`}>
                      ({selectedStock.returnPercent.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setSelectedStock(null)}
                  className="flex-1 bg-transparent border-gray-600/50 text-gray-400 hover:bg-gray-700/50 hover:text-white"
                >
                  닫기
                </Button>
                <Button
                  onClick={() => {
                    console.log(`${selectedStock.symbol} 거래`)
                    setSelectedStock(null)
                  }}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                >
                  거래하기
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
