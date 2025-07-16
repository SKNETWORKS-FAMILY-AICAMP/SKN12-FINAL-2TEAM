"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NotificationList } from "@/components/notifications/notification-list"
import { NotificationSettings } from "@/components/notifications/notification-settings"
import { Bell, Settings, CheckCircle, AlertTriangle, Info, Zap } from "lucide-react"

export default function NotificationsPage() {
  const [activeTab, setActiveTab] = useState("all")

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">알림 센터</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">중요한 트레이딩 알림과 시장 소식을 확인하세요</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="bg-white/80 dark:bg-slate-800/80">
            <CheckCircle className="h-4 w-4 mr-2" />
            모두 읽음
          </Button>
          <Button variant="outline" className="bg-white/80 dark:bg-slate-800/80">
            <Settings className="h-4 w-4 mr-2" />
            알림 설정
          </Button>
        </div>
      </div>

      {/* Notification Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-0 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 professional-shadow">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
                <Bell className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">전체 알림</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">24개</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 bg-gradient-to-br from-red-50 to-pink-50 dark:from-red-900/20 dark:to-pink-900/20 professional-shadow">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-gradient-to-br from-red-500 to-pink-600 text-white">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">읽지 않음</p>
                <p className="text-2xl font-bold text-red-600">3개</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 professional-shadow">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 text-white">
                <Zap className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">트레이딩 알림</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">8개</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 professional-shadow">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 text-white">
                <Info className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">시장 소식</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">13개</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
              <Bell className="h-5 w-5" />
            </div>
            알림 목록
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-5 bg-gray-100 dark:bg-slate-700">
              <TabsTrigger value="all">전체</TabsTrigger>
              <TabsTrigger value="trading">트레이딩</TabsTrigger>
              <TabsTrigger value="market">시장</TabsTrigger>
              <TabsTrigger value="ai">AI</TabsTrigger>
              <TabsTrigger value="system">시스템</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="space-y-4">
              <NotificationList filter="all" />
            </TabsContent>

            <TabsContent value="trading" className="space-y-4">
              <NotificationList filter="trading" />
            </TabsContent>

            <TabsContent value="market" className="space-y-4">
              <NotificationList filter="market" />
            </TabsContent>

            <TabsContent value="ai" className="space-y-4">
              <NotificationList filter="ai" />
            </TabsContent>

            <TabsContent value="system" className="space-y-4">
              <NotificationList filter="system" />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <NotificationSettings />
    </div>
  )
}
