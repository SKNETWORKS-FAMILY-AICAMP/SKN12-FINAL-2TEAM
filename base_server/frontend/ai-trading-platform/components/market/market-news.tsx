"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Newspaper, TrendingUp, TrendingDown, Clock, ExternalLink } from "lucide-react"

interface MarketNewsProps {
  detailed?: boolean
}

const news = [
  {
    id: 1,
    title: "삼성전자, 3분기 실적 시장 예상치 상회",
    summary: "삼성전자가 발표한 3분기 실적이 시장 예상치를 크게 상회하며 주가 상승을 견인하고 있습니다.",
    source: "한국경제",
    publishedAt: "2시간 전",
    sentiment: "positive",
    impact: "high",
    relatedStocks: ["삼성전자", "SK하이닉스"],
    category: "실적",
  },
  {
    id: 2,
    title: "연준 금리 동결 전망 강화, 국내 증시에 호재",
    summary: "미 연준의 금리 동결 가능성이 높아지면서 국내 증시에 긍정적인 영향을 미칠 것으로 전망됩니다.",
    source: "매일경제",
    publishedAt: "4시간 전",
    sentiment: "positive",
    impact: "medium",
    relatedStocks: ["KOSPI", "금융주"],
    category: "정책",
  },
  {
    id: 3,
    title: "중국 경제 둔화 우려, 수출 관련주 약세",
    summary: "중국의 경제 성장률 둔화 우려가 확산되면서 중국 수출 의존도가 높은 기업들의 주가가 하락했습니다.",
    source: "서울경제",
    publishedAt: "6시간 전",
    sentiment: "negative",
    impact: "medium",
    relatedStocks: ["화학", "철강"],
    category: "국제",
  },
  {
    id: 4,
    title: "AI 반도체 수요 급증, 관련주 강세 지속",
    summary: "인공지능 반도체에 대한 수요가 급증하면서 관련 기업들의 주가가 강세를 보이고 있습니다.",
    source: "전자신문",
    publishedAt: "8시간 전",
    sentiment: "positive",
    impact: "high",
    relatedStocks: ["SK하이닉스", "삼성전자"],
    category: "기술",
  },
  {
    id: 5,
    title: "바이오 신약 임상 성공, 관련 종목 급등",
    summary: "국내 바이오 기업의 신약 임상시험 성공 소식이 전해지면서 바이오 섹터 전반이 상승세를 보였습니다.",
    source: "바이오스펙테이터",
    publishedAt: "12시간 전",
    sentiment: "positive",
    impact: "medium",
    relatedStocks: ["삼성바이오로직스", "셀트리온"],
    category: "바이오",
  },
]

export function MarketNews({ detailed = false }: MarketNewsProps) {
  const displayNews = detailed ? news : news.slice(0, 3)

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case "negative":
        return <TrendingDown className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-100 text-green-700 border-green-200"
      case "negative":
        return "bg-red-100 text-red-700 border-red-200"
      default:
        return "bg-gray-100 text-gray-700 border-gray-200"
    }
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "high":
        return "bg-red-100 text-red-700 border-red-200"
      case "medium":
        return "bg-yellow-100 text-yellow-700 border-yellow-200"
      case "low":
        return "bg-green-100 text-green-700 border-green-200"
      default:
        return "bg-gray-100 text-gray-700 border-gray-200"
    }
  }

  return (
    <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-3 text-xl">
            <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 text-white">
              <Newspaper className="h-5 w-5" />
            </div>
            시장 뉴스
          </CardTitle>
          {!detailed && (
            <Button variant="outline" size="sm" className="bg-transparent">
              전체 보기
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {displayNews.map((article) => (
          <div
            key={article.id}
            className="p-4 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-slate-700 transition-all duration-300 hover:shadow-md"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">{getSentimentIcon(article.sentiment)}</div>

              <div className="flex-1 space-y-3">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white text-base leading-tight">
                    {article.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 leading-relaxed">{article.summary}</p>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>{article.source}</span>
                    <span>•</span>
                    <span>{article.publishedAt}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={`text-xs ${getSentimentColor(article.sentiment)}`}>
                      {article.sentiment === "positive" ? "긍정" : article.sentiment === "negative" ? "부정" : "중립"}
                    </Badge>
                    <Badge variant="outline" className={`text-xs ${getImpactColor(article.impact)}`}>
                      {article.impact === "high" ? "높음" : article.impact === "medium" ? "중간" : "낮음"}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {article.category}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {article.relatedStocks.map((stock, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {stock}
                      </Badge>
                    ))}
                  </div>

                  <Button variant="ghost" size="sm" className="text-xs">
                    <ExternalLink className="h-3 w-3 mr-1" />
                    원문 보기
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ))}

        {detailed && (
          <div className="text-center pt-4">
            <Button variant="outline" className="bg-transparent">
              더 많은 뉴스 보기
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
