"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MarketIndices } from "@/components/market/market-indices"
import { StockScreener } from "@/components/market/stock-screener"
import { MarketNews } from "@/components/market/market-news"
import { TechnicalAnalysis } from "@/components/market/technical-analysis"
import { TrendingUp, Search, Globe, Newspaper, BarChart3, Filter } from "lucide-react"
import { useKoreaInvestApiStatus } from "@/hooks/use-korea-invest-api-status"
import KoreaInvestApiRequired from "@/components/KoreaInvestApiRequired"

export default function MarketPage() {
  const [activeTab, setActiveTab] = useState("overview")
  const [searchQuery, setSearchQuery] = useState("")
  const { isConfigured, isLoading, error } = useKoreaInvestApiStatus()
  
  // API가 설정되지 않은 경우
  if (!isConfigured) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
        <KoreaInvestApiRequired pageType="dashboard" />
      </div>
    );
  }

  // 로딩 상태 처리
  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-300">API 설정 상태를 확인하는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태 처리
  if (error) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">오류가 발생했습니다: {error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">마켓 분석</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">실시간 시장 데이터와 AI 분석을 확인하세요</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
            시장 개장
          </Badge>
        </div>
      </div>

      {/* Search Bar */}
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="종목명, 종목코드 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-gray-50 dark:bg-slate-700 border-0"
              />
            </div>
            <Button variant="outline" className="bg-transparent">
              <Filter className="h-4 w-4 mr-2" />
              필터
            </Button>
            <Button className="bg-gradient-to-r from-blue-500 to-indigo-600">
              <BarChart3 className="h-4 w-4 mr-2" />
              차트 분석
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Market Indices */}
      <MarketIndices />

      {/* Main Content Tabs */}
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
              <Globe className="h-5 w-5" />
            </div>
            시장 분석
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-4 bg-gray-100 dark:bg-slate-700">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                시장 현황
              </TabsTrigger>
              <TabsTrigger value="screener" className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                종목 스크리너
              </TabsTrigger>
              <TabsTrigger value="technical" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                기술적 분석
              </TabsTrigger>
              <TabsTrigger value="news" className="flex items-center gap-2">
                <Newspaper className="h-4 w-4" />
                뉴스 & 이벤트
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <TechnicalAnalysis />
                <MarketNews />
              </div>
            </TabsContent>

            <TabsContent value="screener" className="space-y-6">
              <StockScreener />
            </TabsContent>

            <TabsContent value="technical" className="space-y-6">
              <TechnicalAnalysis detailed />
            </TabsContent>

            <TabsContent value="news" className="space-y-6">
              <MarketNews detailed />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
