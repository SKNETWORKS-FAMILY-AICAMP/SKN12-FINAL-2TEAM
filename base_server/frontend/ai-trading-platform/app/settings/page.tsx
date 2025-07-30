"use client"

import React, { useState } from "react";
import { Header } from "@/components/layout/header";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { useRouter } from "next/navigation";
import { useTutorial } from "@/hooks/use-tutorial"
import { TutorialOverlay } from "@/components/tutorial/tutorial-overlay"
import { Settings, User, Bell, Shield, CreditCard, LogOut } from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const {
    currentTutorial,
    currentStep,
    currentStepInfo,
    nextStep,
    previousStep,
    skipTutorial,
    isLoading: tutorialLoading
  } = useTutorial();

  const handleNavigate = (key: string) => {
    switch (key) {
      case "dashboard":
        router.push("/dashboard"); break;
      case "portfolio":
        router.push("/portfolio"); break;
      case "signals":
        router.push("/autotrade"); break;
      case "chat":
        router.push("/chat"); break;
      case "settings":
        router.push("/settings"); break;
      default:
        break;
    }
    setSidebarOpen(false);
  };

  return (
    <div className="h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white overflow-hidden">
      <Header onSidebarOpen={() => setSidebarOpen(true)} />
      <AppSidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
        onNavigate={handleNavigate}
      />
      <main className="flex flex-col items-center px-6 md:px-12 py-8 bg-transparent h-full overflow-y-auto">
        <div className="w-full max-w-4xl">
          <h1 className="text-2xl md:text-3xl font-bold mb-4 tracking-tight text-white">
            개인 정보 설정 
          </h1>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Profile Settings */}
            <div className="metric-card p-6 settings-section">
              <div className="flex items-center gap-3 mb-6">
                <User className="text-blue-400" size={24} />
                <h2 className="text-xl font-semibold text-white">프로필 설정</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">전화번호</label>
                  <input
                    type="text"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="휴대폰 번호을 입력하세요"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">이메일</label>
                  <input
                    type="email"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="이메일을 입력하세요"
                  />
                </div>
              </div>
            </div>

            {/* Notification Settings */}
            <div className="metric-card p-6 notification-settings">
              <div className="flex items-center gap-3 mb-6">
                <Bell className="text-green-400" size={24} />
                <h2 className="text-xl font-semibold text-white">알림 설정</h2>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">이메일 알림</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">메세지 알림</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

              </div>
            </div>

            {/* Security Settings */}
            <div className="metric-card p-6">
              <div className="flex items-center gap-3 mb-6">
                <Shield className="text-red-400" size={24} />
                <h2 className="text-xl font-semibold text-white">보안 설정</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">현재 비밀번호</label>
                  <input
                    type="password"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="현재 비밀번호를 입력하세요"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">새 비밀번호</label>
                  <input
                    type="password"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="새 비밀번호를 입력하세요"
                  />
                </div>
              </div>
            </div>

            {/* Billing Settings */}
            <div className="metric-card p-6">
              <div className="flex items-center gap-3 mb-6">
                <CreditCard className="text-purple-400" size={24} />
                <h2 className="text-xl font-semibold text-white">결제 설정</h2>
              </div>
              <div className="space-y-4">
                <div className="p-4 bg-gray-800 rounded-lg">
                  <div className="text-sm text-gray-400">현재 플랜</div>
                  <div className="text-lg font-semibold text-white">프리미엄 플랜</div>
                  <div className="text-sm text-gray-400">₩29,900/월</div>
                </div>
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors">
                  플랜 변경
                </button>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-8 text-center">
            <div className="flex gap-4 justify-center">
              <button className="flex items-center gap-2 bg-gray-600 hover:bg-gray-700 text-white py-3 px-6 rounded-lg transition-colors">
                <LogOut size={16} />
                초기 설정 복구
              </button>
              <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg transition-colors">
                <LogOut size={16} />
                변경 사항 적용
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* 튜토리얼 오버레이 */}
      <TutorialOverlay
        isVisible={!!currentTutorial && !!currentStepInfo()}
        stepInfo={currentStepInfo()}
        onNext={nextStep}
        onPrevious={previousStep}
        onSkip={skipTutorial}
        currentStep={currentStep}
        totalSteps={currentTutorial === 'SETTINGS' ? 3 : 0}
      />
    </div>
  );
} 