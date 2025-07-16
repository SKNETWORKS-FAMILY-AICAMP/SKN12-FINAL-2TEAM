"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Filter, TrendingUp, TrendingDown } from "lucide-react"

const stocks = [
  {
    symbol: "005930",
    name: "삼성전자",
    price: 68500,
    change: 1500,
    changePercent: 2.24,
    volume: "15.2M",
    marketCap: "408조",
    sector: "기술",
    pe: 12.5,
    pbr: 1.2,
  },
  {
    symbol: "000660",
    name: "SK하이닉스",
    price: 115000,
    change: -2500,
    changePercent: -2.13,
    volume: "8.7M",
    marketCap: "84조",
    sector: "반도체",
    pe: 15.8,
    pbr: 1.8,
  },
  {
    symbol: "035420",
    name: "NAVER",
    price: 185000,
    change: 3500,
    changePercent: 1.93,
    volume: "2.1M",
    marketCap: "30조",
    sector: "인터넷",
    pe: 18.2,
    pbr: 2.1,
  },
  {
    symbol: "035720",
    name: "카카오",
    price: 48500,
    change: -1200,
    changePercent: -2.41,
    volume: "5.8M",
    marketCap: "21조",
    sector: "인터넷",
    pe: 22.1,
    pbr: 1.5,
  },
  {
    symbol: "207940",
    name: "삼성바이오로직스",
    price: 785000,
    change: 15000,
    changePercent: 1.95,
    volume: "0.3M",
    marketCap: "112조",
    sector: "바이오",
    pe: 45.2,
    pbr: 3.8,
  },
]

export function StockScreener() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedSector, setSelectedSector] = useState("all")
  const [sortBy, setSortBy] = useState("marketCap")

  const filteredStocks = stocks
    .filter((stock) => {
      const matchesSearch =
        stock.name.toLowerCase().includes(searchTerm.toLowerCase()) || stock.symbol.includes(searchTerm)
      const matchesSector = selectedSector === "all" || stock.sector === selectedSector
      return matchesSearch && matchesSector
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "price":
          return b.price - a.price
        case "change":
          return b.changePercent - a.changePercent
        case "volume":
          return Number.parseFloat(b.volume) - Number.parseFloat(a.volume)
        default:
          return 0
      }
    })

  return (
    <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3 text-xl">
          <div className="p-2 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white">
            <Search className="h-5 w-5" />
          </div>
          종목 스크리너
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="종목명 또는 코드 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <Select value={selectedSector} onValueChange={setSelectedSector}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="섹터 선택" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체 섹터</SelectItem>
              <SelectItem value="기술">기술</SelectItem>
              <SelectItem value="반도체">반도체</SelectItem>
              <SelectItem value="인터넷">인터넷</SelectItem>
              <SelectItem value="바이오">바이오</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="정렬 기준" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="marketCap">시가총액</SelectItem>
              <SelectItem value="price">주가</SelectItem>
              <SelectItem value="change">등락률</SelectItem>
              <SelectItem value="volume">거래량</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" className="bg-transparent">
            <Filter className="h-4 w-4 mr-2" />
            고급 필터
          </Button>
        </div>

        {/* Results */}
        <div className="space-y-3">
          {filteredStocks.map((stock) => (
            <div
              key={stock.symbol}
              className="p-4 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-slate-700 transition-all duration-300 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold">
                    {stock.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white text-lg">{stock.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-sm text-gray-500 dark:text-gray-400">{stock.symbol}</span>
                      <Badge variant="outline" className="text-xs">
                        {stock.sector}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-8">
                  <div className="text-right">
                    <div className="text-xl font-bold text-gray-900 dark:text-white">
                      ₩{stock.price.toLocaleString()}
                    </div>
                    <div className="flex items-center gap-1">
                      {stock.change > 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                      <span className={`text-sm font-medium ${stock.change > 0 ? "text-green-600" : "text-red-600"}`}>
                        {stock.change > 0 ? "+" : ""}
                        {stock.change.toLocaleString()}({stock.changePercent > 0 ? "+" : ""}
                        {stock.changePercent.toFixed(2)}%)
                      </span>
                    </div>
                  </div>

                  <div className="text-right text-sm text-gray-600 dark:text-gray-400">
                    <div>거래량: {stock.volume}</div>
                    <div>시총: {stock.marketCap}</div>
                  </div>

                  <div className="text-right text-sm text-gray-600 dark:text-gray-400">
                    <div>PER: {stock.pe}</div>
                    <div>PBR: {stock.pbr}</div>
                  </div>

                  <Button variant="outline" size="sm" className="bg-transparent">
                    상세보기
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredStocks.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>검색 조건에 맞는 종목이 없습니다.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
