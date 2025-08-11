"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Settings, Download, Calendar, BarChart3, PieChart, TrendingUp, FileText } from "lucide-react"

export function CustomReport() {
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
    "performance",
    "risk",
    "allocation"
  ])
  const [reportFrequency, setReportFrequency] = useState("monthly")
  const [autoGenerate, setAutoGenerate] = useState(true)
  const [emailNotification, setEmailNotification] = useState(false)

  const availableMetrics = [
    { id: "performance", name: "성과 분석", description: "수익률, 벤치마크 비교, 알파/베타" },
    { id: "risk", name: "리스크 분석", description: "VaR, 최대낙폭, 변동성 지표" },
    { id: "allocation", name: "자산 배분", description: "섹터별, 지역별, 자산군별 분산" },
    { id: "trading", name: "거래 분석", description: "거래 빈도, 회전율, 수수료" },
    { id: "tax", name: "세무 분석", description: "과세 소득, 절세 전략" },
    { id: "esg", name: "ESG 분석", description: "지속가능성 투자 지표" },
  ]

  const reportTemplates = [
    { id: "executive", name: "경영진 요약", description: "핵심 지표 중심의 간결한 리포트" },
    { id: "detailed", name: "상세 분석", description: "모든 지표를 포함한 종합 리포트" },
    { id: "compliance", name: "컴플라이언스", description: "규제 준수를 위한 리포트" },
    { id: "investor", name: "투자자용", description: "투자자 대상 성과 리포트" },
  ]

  const toggleMetric = (metricId: string) => {
    setSelectedMetrics(prev => 
      prev.includes(metricId)
        ? prev.filter(id => id !== metricId)
        : [...prev, metricId]
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">맞춤 리포트 설정</h2>
        <div className="flex gap-3">
          <Button variant="outline">
            <Settings className="w-4 h-4 mr-2" />
            템플릿 저장
          </Button>
          <Button className="bg-blue-500 hover:bg-blue-600 text-white">
            <Download className="w-4 h-4 mr-2" />
            리포트 생성
          </Button>
        </div>
      </div>

      {/* Report Templates */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            리포트 템플릿
          </CardTitle>
          <CardDescription>
            사전 정의된 템플릿을 선택하거나 직접 커스터마이징하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reportTemplates.map((template) => (
              <div 
                key={template.id}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900 dark:text-white">{template.name}</h4>
                  <Badge variant="outline" className="text-xs">템플릿</Badge>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{template.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Custom Metrics Selection */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieChart className="w-5 h-5 text-green-500" />
            포함할 지표 선택
          </CardTitle>
          <CardDescription>
            리포트에 포함할 분석 지표를 선택하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableMetrics.map((metric) => (
              <div 
                key={metric.id}
                className="flex items-start space-x-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <Checkbox
                  id={metric.id}
                  checked={selectedMetrics.includes(metric.id)}
                  onCheckedChange={() => toggleMetric(metric.id)}
                  className="mt-1"
                />
                <div className="flex-1">
                  <label 
                    htmlFor={metric.id}
                    className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer"
                  >
                    {metric.name}
                  </label>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {metric.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Report Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-purple-500" />
              생성 설정
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                리포트 생성 주기
              </label>
              <Select value={reportFrequency} onValueChange={setReportFrequency}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">매일</SelectItem>
                  <SelectItem value="weekly">매주</SelectItem>
                  <SelectItem value="monthly">매월</SelectItem>
                  <SelectItem value="quarterly">분기별</SelectItem>
                  <SelectItem value="yearly">연간</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  자동 생성
                </h4>
                <p className="text-xs text-gray-500">
                  설정된 주기에 따라 자동으로 리포트 생성
                </p>
              </div>
              <Switch
                checked={autoGenerate}
                onCheckedChange={setAutoGenerate}
                className="data-[state=checked]:bg-blue-500"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  이메일 알림
                </h4>
                <p className="text-xs text-gray-500">
                  리포트 생성 시 이메일로 알림 발송
                </p>
              </div>
              <Switch
                checked={emailNotification}
                onCheckedChange={setEmailNotification}
                className="data-[state=checked]:bg-blue-500"
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              리포트 미리보기
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200">
                <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                  선택된 지표: {selectedMetrics.length}개
                </h4>
                <div className="flex flex-wrap gap-1">
                  {selectedMetrics.map((metricId) => {
                    const metric = availableMetrics.find(m => m.id === metricId)
                    return (
                      <Badge key={metricId} variant="outline" className="text-xs">
                        {metric?.name}
                      </Badge>
                    )
                  })}
                </div>
              </div>

              <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200">
                <h4 className="text-sm font-semibold text-green-900 dark:text-green-100 mb-2">
                  생성 주기
                </h4>
                <p className="text-sm text-green-700 dark:text-green-300">
                  {reportFrequency === "daily" && "매일"}
                  {reportFrequency === "weekly" && "매주"}
                  {reportFrequency === "monthly" && "매월"}
                  {reportFrequency === "quarterly" && "분기별"}
                  {reportFrequency === "yearly" && "연간"}
                  {autoGenerate ? " 자동 생성" : " 수동 생성"}
                </p>
              </div>

              <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200">
                <h4 className="text-sm font-semibold text-purple-900 dark:text-purple-100 mb-2">
                  예상 페이지 수
                </h4>
                <p className="text-sm text-purple-700 dark:text-purple-300">
                  약 {selectedMetrics.length * 2 + 3}페이지
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Reports */}
      <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle>최근 생성된 리포트</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>아직 생성된 리포트가 없습니다</p>
              <p className="text-sm">첫 번째 리포트를 생성해보세요</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
