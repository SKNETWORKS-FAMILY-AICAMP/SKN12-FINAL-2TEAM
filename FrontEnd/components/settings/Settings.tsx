"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  PaintBrushIcon,
  CreditCardIcon,
  ChartBarIcon,
  KeyIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline"

const settingsCategories = [
  {
    id: "profile",
    title: "프로필 설정",
    description: "투자 성향과 개인 정보 관리",
    icon: UserIcon,
    color: "from-blue-500 to-blue-600",
    settings: [
      { id: "investment-experience", label: "투자 경험", value: "중급자", type: "select" },
      { id: "risk-tolerance", label: "위험 선호도", value: "중간", type: "select" },
      { id: "investment-goals", label: "투자 목표", value: "자산 증식", type: "select" },
      { id: "monthly-budget", label: "월 투자 예산", value: "100만원", type: "select" },
    ],
  },
  {
    id: "notifications",
    title: "알림 설정",
    description: "시장 알림과 포트폴리오 알림",
    icon: BellIcon,
    color: "from-yellow-500 to-yellow-600",
    settings: [
      { id: "price-alerts", label: "가격 변동 알림", value: true, type: "toggle" },
      { id: "news-alerts", label: "뉴스 알림", value: true, type: "toggle" },
      { id: "portfolio-alerts", label: "포트폴리오 알림", value: false, type: "toggle" },
      { id: "trading-alerts", label: "거래 완료 알림", value: true, type: "toggle" },
    ],
  },
  {
    id: "security",
    title: "보안 설정",
    description: "계정 보안과 개인정보 보호",
    icon: ShieldCheckIcon,
    color: "from-green-500 to-green-600",
    settings: [
      { id: "two-factor", label: "2단계 인증", value: false, type: "toggle" },
      { id: "biometric", label: "생체 인증", value: true, type: "toggle" },
      { id: "session-timeout", label: "세션 타임아웃", value: "30분", type: "select" },
      { id: "login-alerts", label: "로그인 알림", value: true, type: "toggle" },
    ],
  },
  {
    id: "display",
    title: "화면 설정",
    description: "테마 및 레이아웃 커스터마이징",
    icon: PaintBrushIcon,
    color: "from-purple-500 to-purple-600",
    settings: [
      { id: "theme", label: "테마", value: "다크", type: "select" },
      { id: "language", label: "언어", value: "한국어", type: "select" },
      { id: "currency", label: "기본 통화", value: "KRW", type: "select" },
      { id: "chart-style", label: "차트 스타일", value: "캔들", type: "select" },
    ],
  },
  {
    id: "trading",
    title: "거래 설정",
    description: "자동매매 및 거래 환경 설정",
    icon: ChartBarIcon,
    color: "from-red-500 to-red-600",
    settings: [
      { id: "auto-trading", label: "자동매매 활성화", value: true, type: "toggle" },
      { id: "max-position", label: "최대 포지션 크기", value: "10%", type: "select" },
      { id: "stop-loss", label: "손절매 설정", value: "-5%", type: "select" },
      { id: "take-profit", label: "익절매 설정", value: "+15%", type: "select" },
    ],
  },
  {
    id: "account",
    title: "계정 관리",
    description: "구독, 결제 및 계정 정보",
    icon: CreditCardIcon,
    color: "from-indigo-500 to-indigo-600",
    settings: [
      { id: "subscription", label: "구독 플랜", value: "PRO", type: "info" },
      { id: "billing", label: "결제 정보", value: "카드 ****1234", type: "info" },
      { id: "api-access", label: "API 접근", value: "활성화", type: "info" },
      { id: "data-export", label: "데이터 내보내기", value: "", type: "action" },
    ],
  },
]

export default function Settings() {
  const [selectedCategory, setSelectedCategory] = useState("profile")
  const [settings, setSettings] = useState<Record<string, any>>({})

  const currentCategory = settingsCategories.find((cat) => cat.id === selectedCategory)

  const handleToggle = (settingId: string, currentValue: boolean) => {
    setSettings((prev) => ({
      ...prev,
      [settingId]: !currentValue,
    }))
  }

  const handleSave = () => {
    console.log("설정 저장:", settings)
    // 실제 저장 로직
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">설정</h1>
        <p className="text-gray-300">계정 설정과 개인화 옵션을 관리하세요</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* 사이드바 */}
        <div className="lg:col-span-1">
          <Card className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 shadow-xl">
            <CardContent className="p-0">
              <nav className="space-y-1">
                {settingsCategories.map((category) => {
                  const IconComponent = category.icon
                  return (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category.id)}
                      className={`w-full flex items-center space-x-3 px-4 py-3 text-left transition-all duration-200 ${
                        selectedCategory === category.id
                          ? "bg-gradient-to-r from-blue-500/20 to-purple-500/20 border-r-2 border-blue-500 text-white"
                          : "text-gray-300 hover:bg-gray-800/50 hover:text-white"
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-lg bg-gradient-to-r ${category.color} flex items-center justify-center`}
                      >
                        <IconComponent className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="font-medium">{category.title}</div>
                        <div className="text-xs text-gray-400">{category.description}</div>
                      </div>
                    </button>
                  )
                })}
              </nav>
            </CardContent>
          </Card>
        </div>

        {/* 메인 설정 영역 */}
        <div className="lg:col-span-3">
          {currentCategory && (
            <Card className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 shadow-xl">
              <CardHeader className="border-b border-gray-800/50">
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-10 h-10 rounded-lg bg-gradient-to-r ${currentCategory.color} flex items-center justify-center`}
                  >
                    <currentCategory.icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-white">{currentCategory.title}</CardTitle>
                    <p className="text-gray-400 text-sm">{currentCategory.description}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                {currentCategory.settings.map((setting) => (
                  <div
                    key={setting.id}
                    className="flex items-center justify-between py-3 border-b border-gray-800/30 last:border-b-0"
                  >
                    <div>
                      <label className="text-white font-medium">{setting.label}</label>
                    </div>

                    <div className="flex items-center space-x-3">
                      {setting.type === "toggle" && (
                        <button
                          onClick={() => handleToggle(setting.id, setting.value)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            (settings[setting.id] ?? setting.value) ? "bg-blue-500" : "bg-gray-600"
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              (settings[setting.id] ?? setting.value) ? "translate-x-6" : "translate-x-1"
                            }`}
                          />
                        </button>
                      )}

                      {setting.type === "select" && (
                        <select className="bg-gray-800/50 border border-gray-700/50 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                          <option>{setting.value}</option>
                        </select>
                      )}

                      {setting.type === "info" && (
                        <span className="text-gray-300 bg-gray-800/50 px-3 py-2 rounded-lg">{setting.value}</span>
                      )}

                      {setting.type === "action" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50"
                        >
                          실행
                        </Button>
                      )}
                    </div>
                  </div>
                ))}

                {/* 특별 설정들 */}
                {selectedCategory === "security" && (
                  <div className="mt-6 space-y-4">
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <KeyIcon className="w-5 h-5 text-yellow-400" />
                        <span className="text-yellow-400 font-medium">보안 강화 권장</span>
                      </div>
                      <p className="text-gray-300 text-sm">계정 보안을 위해 2단계 인증을 활성화하는 것을 권장합니다.</p>
                      <Button size="sm" className="mt-3 bg-yellow-500 hover:bg-yellow-600 text-black">
                        2단계 인증 설정
                      </Button>
                    </div>
                  </div>
                )}

                {selectedCategory === "account" && (
                  <div className="mt-6 space-y-4">
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <CheckCircleIcon className="w-5 h-5 text-blue-400" />
                        <span className="text-blue-400 font-medium">PRO 구독 활성화</span>
                      </div>
                      <p className="text-gray-300 text-sm">고급 분석 도구와 자동매매 기능을 이용하실 수 있습니다.</p>
                      <div className="flex space-x-3 mt-3">
                        <Button
                          size="sm"
                          variant="outline"
                          className="bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50"
                        >
                          구독 관리
                        </Button>
                        <Button size="sm" className="bg-blue-500 hover:bg-blue-600">
                          업그레이드
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 저장 버튼 */}
                <div className="flex justify-end pt-6 border-t border-gray-800/50">
                  <div className="flex space-x-3">
                    <Button
                      variant="outline"
                      className="bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50"
                    >
                      초기화
                    </Button>
                    <Button
                      onClick={handleSave}
                      className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                    >
                      변경사항 저장
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
