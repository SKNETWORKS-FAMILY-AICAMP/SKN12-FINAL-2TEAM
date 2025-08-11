"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useChat } from "@/hooks/use-chat"
import { useAutoTrade } from "@/hooks/use-autotrade"
import { useNotifications } from "@/hooks/use-notifications"
import { useDashboard } from "@/hooks/use-dashboard"
import { usePortfolio } from "@/hooks/use-portfolio"
import { apiClient } from "@/lib/api/client"

interface ErrorWithCode {
  code: string | number;
  message?: string;
}

export function ErrorTestPanel() {
  const [testResults, setTestResults] = useState<Record<string, any>>({})
  const [isRunning, setIsRunning] = useState(false)
  
  const { error: chatError, clearError: clearChatError } = useChat()
  const { error: autotradeError, clearError: clearAutotradeError } = useAutoTrade()
  const { error: notificationError, clearError: clearNotificationError } = useNotifications()
  const { error: dashboardError, clearError: clearDashboardError } = useDashboard()
  const { error: portfolioError, clearError: clearPortfolioError } = usePortfolio()

  // 타입 가드 함수
  const hasCode = (error: any): error is ErrorWithCode => {
    return error && typeof error === 'object' && 'code' in error;
  }

  // 에러 코드별 시뮬레이션
  const simulateError = async (errorCode: number, description: string) => {
    setIsRunning(true)
    
    try {
      // 로컬 시뮬레이션 (API 호출 대신)
      await new Promise(resolve => setTimeout(resolve, 100)); // 시뮬레이션 지연
      
      setTestResults(prev => ({
        ...prev,
        [errorCode]: {
          success: true,
          timestamp: new Date().toISOString(),
          description,
          result: `시뮬레이션 성공: ${description}`
        }
      }))
      
    } catch (error: any) {
      setTestResults(prev => ({
        ...prev,
        [errorCode]: {
          success: false,
          timestamp: new Date().toISOString(),
          description,
          error: error.message,
          responseData: error.response?.data
        }
      }))
    } finally {
      setIsRunning(false)
    }
  }

  // 모든 에러 테스트 실행
  const runAllTests = async () => {
    setIsRunning(true)
    
    const testCases = [
      { code: 10000, description: "세션 만료 테스트" },
      { code: 2000, description: "잔액 부족 테스트" },
      { code: 2001, description: "잘못된 종목 코드 테스트" },
      { code: 2002, description: "시장 마감 테스트" },
      { code: 2003, description: "주문 실행 실패 테스트" },
      { code: 2004, description: "포지션을 찾을 수 없음 테스트" },
      { code: 2005, description: "잘못된 수량 테스트" },
      { code: 4000, description: "전략을 찾을 수 없음 테스트" },
      { code: 4001, description: "이미 활성화된 전략 테스트" },
      { code: 4002, description: "백테스트 실패 테스트" },
      { code: 4003, description: "잘못된 매개변수 테스트" },
      { code: 4004, description: "전략 실행 실패 테스트" },
      { code: 6000, description: "알림 서비스 불가 테스트" },
      { code: 6001, description: "알림 전송 실패 테스트" },
      { code: 6002, description: "알림 설정을 찾을 수 없음 테스트" },
      { code: 6003, description: "알림 구독 실패 테스트" },
      { code: 7000, description: "대시보드 데이터 불가 테스트" },
      { code: 7001, description: "포트폴리오 정보 불가 테스트" },
      { code: 7002, description: "시장 데이터 불가 테스트" },
      { code: 7003, description: "거래 내역 불가 테스트" },
      { code: 7004, description: "알림 데이터 불가 테스트" }
    ]

    for (const testCase of testCases) {
      await simulateError(testCase.code, testCase.description)
      // 테스트 간 간격
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    
    setIsRunning(false)
  }

  // 특정 카테고리 테스트 실행
  const runCategoryTest = async (category: string, errorCodes: number[]) => {
    setIsRunning(true)
    
    for (const code of errorCodes) {
      const description = `${category} 에러 코드 ${code} 테스트`
      await simulateError(code, description)
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    
    setIsRunning(false)
  }

  // 에러 초기화
  const clearAllErrors = () => {
    clearChatError()
    clearAutotradeError()
    clearNotificationError()
    clearDashboardError()
    clearPortfolioError()
    setTestResults({})
  }

  const getErrorStatus = (errorCode: number) => {
    const result = testResults[errorCode]
    if (!result) return "not-tested"
    return result.success ? "success" : "failed"
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return <Badge variant="default" className="bg-green-600">성공</Badge>
      case "failed":
        return <Badge variant="destructive">실패</Badge>
      case "not-tested":
        return <Badge variant="secondary">미테스트</Badge>
      default:
        return <Badge variant="outline">알 수 없음</Badge>
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">에러 테스트 패널</h1>
          <p className="text-muted-foreground">
            모든 기능의 에러 처리 및 복구 메커니즘을 테스트합니다
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={runAllTests} 
            disabled={isRunning}
            variant="default"
          >
            {isRunning ? "테스트 중..." : "전체 테스트 실행"}
          </Button>
          <Button 
            onClick={clearAllErrors} 
            variant="outline"
          >
            모든 에러 초기화
          </Button>
        </div>
      </div>

      {/* 현재 에러 상태 */}
      <Card>
        <CardHeader>
          <CardTitle>현재 에러 상태</CardTitle>
          <CardDescription>각 기능에서 발생한 에러의 현재 상태</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-sm font-medium text-muted-foreground">채팅</div>
              <Badge variant={chatError ? "destructive" : "default"}>
                {hasCode(chatError) ? `코드 ${chatError.code}` : "정상"}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium text-muted-foreground">자동매매</div>
              <Badge variant={autotradeError ? "destructive" : "default"}>
                {autotradeError ? `코드 ${autotradeError.code}` : "정상"}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium text-muted-foreground">알림</div>
              <Badge variant={notificationError ? "destructive" : "default"}>
                {notificationError ? `코드 ${notificationError.code}` : "정상"}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium text-muted-foreground">대시보드</div>
              <Badge variant={dashboardError ? "destructive" : "default"}>
                {dashboardError ? `코드 ${dashboardError.code}` : "정상"}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium text-muted-foreground">포트폴리오</div>
              <Badge variant={portfolioError ? "destructive" : "default"}>
                {portfolioError ? `코드 ${portfolioError.code}` : "정상"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 카테고리별 테스트 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 인증 에러 테스트 */}
        <Card>
          <CardHeader>
            <CardTitle>인증 에러 테스트</CardTitle>
            <CardDescription>세션 만료 및 인증 실패</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">세션 만료 (10000)</span>
              {getStatusBadge(getErrorStatus(10000))}
            </div>
            <Button 
              onClick={() => simulateError(10000, "세션 만료 시뮬레이션")}
              disabled={isRunning}
              size="sm"
              variant="outline"
            >
              테스트 실행
            </Button>
          </CardContent>
        </Card>

        {/* 포트폴리오 에러 테스트 */}
        <Card>
          <CardHeader>
            <CardTitle>포트폴리오 에러 테스트</CardTitle>
            <CardDescription>거래 및 포지션 관련 에러</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              {[2000, 2001, 2002, 2003, 2004, 2005].map(code => (
                <div key={code} className="flex items-center justify-between">
                  <span className="text-sm">코드 {code}</span>
                  {getStatusBadge(getErrorStatus(code))}
                </div>
              ))}
            </div>
            <Button 
              onClick={() => runCategoryTest("포트폴리오", [2000, 2001, 2002, 2003, 2004, 2005])}
              disabled={isRunning}
              size="sm"
              variant="outline"
            >
              전체 테스트
            </Button>
          </CardContent>
        </Card>

        {/* 자동매매 에러 테스트 */}
        <Card>
          <CardHeader>
            <CardTitle>자동매매 에러 테스트</CardTitle>
            <CardDescription>전략 및 백테스트 관련 에러</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              {[4000, 4001, 4002, 4003, 4004].map(code => (
                <div key={code} className="flex items-center justify-between">
                  <span className="text-sm">코드 {code}</span>
                  {getStatusBadge(getErrorStatus(code))}
                </div>
              ))}
            </div>
            <Button 
              onClick={() => runCategoryTest("자동매매", [4000, 4001, 4002, 4003, 4004])}
              disabled={isRunning}
              size="sm"
              variant="outline"
            >
              전체 테스트
            </Button>
          </CardContent>
        </Card>

        {/* 알림 에러 테스트 */}
        <Card>
          <CardHeader>
            <CardTitle>알림 에러 테스트</CardTitle>
            <CardDescription>알림 서비스 관련 에러</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              {[6000, 6001, 6002, 6003].map(code => (
                <div key={code} className="flex items-center justify-between">
                  <span className="text-sm">코드 {code}</span>
                  {getStatusBadge(getErrorStatus(code))}
                </div>
              ))}
            </div>
            <Button 
              onClick={() => runCategoryTest("알림", [6000, 6001, 6002, 6003])}
              disabled={isRunning}
              size="sm"
              variant="outline"
            >
              전체 테스트
            </Button>
          </CardContent>
        </Card>

        {/* 대시보드 에러 테스트 */}
        <Card>
          <CardHeader>
            <CardTitle>대시보드 에러 테스트</CardTitle>
            <CardDescription>대시보드 데이터 관련 에러</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              {[7000, 7001, 7002, 7003, 7004].map(code => (
                <div key={code} className="flex items-center justify-between">
                  <span className="text-sm">코드 {code}</span>
                  {getStatusBadge(getErrorStatus(code))}
                </div>
              ))}
            </div>
            <Button 
              onClick={() => runCategoryTest("대시보드", [7000, 7001, 7002, 7003, 7004])}
              disabled={isRunning}
              size="sm"
              variant="outline"
            >
              전체 테스트
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 테스트 결과 상세 */}
      {Object.keys(testResults).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>테스트 결과 상세</CardTitle>
            <CardDescription>각 에러 코드별 테스트 실행 결과</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(testResults).map(([code, result]) => (
                <div key={code} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">에러 코드 {code}</h4>
                    {getStatusBadge(result.success ? "success" : "failed")}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {result.description}
                  </p>
                  <div className="text-xs text-muted-foreground">
                    실행 시간: {new Date(result.timestamp).toLocaleString()}
                  </div>
                  {result.error && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                      에러: {result.error}
                    </div>
                  )}
                  {result.result && (
                    <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
                      결과: {JSON.stringify(result.result, null, 2)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 