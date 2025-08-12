"use client"

import React, { useState, useEffect } from "react";
import { Header } from "@/components/layout/header";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { useRouter } from "next/navigation";
import { useTutorial } from "@/hooks/use-tutorial"
import { TutorialOverlay } from "@/components/tutorial/tutorial-overlay"
import { Settings, User, Bell, Shield, CreditCard, LogOut } from "lucide-react";
import { useProfile } from "@/hooks/use-profile";
import { endRouteProgress } from "@/lib/route-progress";

export default function SettingsPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [message, setMessage] = useState("");
  
  // Profile 훅 사용
  const {
    profileData,
    notificationSettings,
    loading,
    error,
    loadProfile,
    updateProfile,
    updateNotifications,
    changePassword,
    saveApiKeys,
    clearError,
    hasProfileChanges,
    setProfileData,
    setNotificationSettings
  } = useProfile();

  // Password change state
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
    otpCode: ""
  });
  const [changingPassword, setChangingPassword] = useState(false);

  const {
    currentTutorial,
    currentStep,
    currentStepInfo,
    nextStep,
    previousStep,
    skipTutorial,
    isLoading: tutorialLoading
  } = useTutorial();

  // Load data on component mount
  useEffect(() => {
    const abortController = new AbortController();
    let isMounted = true;
    
    const loadDataSafely = async () => {
      if (abortController.signal.aborted || !isMounted) return;
      await loadProfile();
    };
    
    loadDataSafely();
    
    return () => {
      isMounted = false;
      abortController.abort();
    };
  }, [loadProfile]);

  // Error 처리
  useEffect(() => {
    if (error) {
      setMessage(error);
    }
  }, [error]);

  const handleSave = async () => {
    try {
      setMessage("");
      
      // 프로필 데이터 변경사항이 있는 경우
      if (hasProfileChanges()) {
        // 필수 필드 검증 (닉네임, 이메일, 전화번호)
        if (!profileData.nickname || profileData.nickname.trim() === "") {
          setMessage("닉네임을 입력해주세요.");
          return;
        }
        
        if (!profileData.email || profileData.email.trim() === "") {
          setMessage("이메일을 입력해주세요.");
          return;
        }
        
        if (!profileData.phone_number || profileData.phone_number.trim() === "") {
          setMessage("전화번호를 입력해주세요.");
          return;
        }
        
        // 프로필 업데이트 (updateAllProfile에서 notificationSettings도 함께 처리)
        const profileResult = await updateProfile(profileData);
        if (!profileResult.success) {
          setMessage(profileResult.error || "프로필 업데이트에 실패했습니다.");
          return;
        }
      } else {
        // 프로필 데이터 변경사항이 없는 경우 알림 설정만 업데이트
        const notificationResult = await updateNotifications({});
        if (!notificationResult.success) {
          setMessage(notificationResult.error || "알림 설정 업데이트에 실패했습니다.");
          return;
        }
      }
      
      setMessage("설정이 성공적으로 저장되었습니다.");
      
      // 3초 후 메시지 제거
      setTimeout(() => {
        setMessage("");
      }, 3000);
      
    } catch (error) {
      console.error("Failed to save settings:", error);
      setMessage("설정 저장에 실패했습니다.");
    }
  };

  const handleProfileChange = (field: string, value: string) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSettingsChange = (field: string, value: any) => {
    setNotificationSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePasswordChange = (field: string, value: string) => {
    setPasswordData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleChangePassword = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setMessage("새 비밀번호가 일치하지 않습니다.");
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setMessage("새 비밀번호는 최소 6자 이상이어야 합니다.");
      return;
    }

    if (!passwordData.currentPassword || passwordData.currentPassword.trim() === "") {
      setMessage("현재 비밀번호를 입력해주세요.");
      return;
    }

    if (!passwordData.newPassword || passwordData.newPassword.trim() === "") {
      setMessage("새 비밀번호를 입력해주세요.");
      return;
    }

    try {
      setChangingPassword(true);
      setMessage("");

      // 현재 비밀번호와 새 비밀번호로 변경
      const response = await changePassword(
        passwordData.currentPassword,
        passwordData.newPassword
      );

      // 응답이 문자열인 경우 파싱
      const responseData = typeof response === 'string' ? JSON.parse(response) : response;

      if (responseData.success) {
        setMessage("비밀번호가 성공적으로 변경되었습니다.");
        setPasswordData({
          currentPassword: "",
          newPassword: "",
          confirmPassword: "",
          otpCode: ""
        });
        
        // 비밀번호 변경 후 재로그인 필요
        if (responseData.require_relogin) {
          setTimeout(() => {
            window.location.href = "/auth/login";
          }, 2000);
        }
      } else {
        // errorCode에 따른 특별 처리
        if (responseData.errorCode === 9004) {
          setMessage("현재 비밀번호가 일치하지 않습니다.");
        } else {
          setMessage(responseData.error || "비밀번호 변경에 실패했습니다.");
        }
      }
    } catch (error: any) {
      console.error("Failed to change password:", error);
      
      // 에러 타입에 따른 메시지 처리
      if (error.response?.status === 404) {
        setMessage("비밀번호 변경 API를 찾을 수 없습니다.");
      } else if (error.response?.status === 400) {
        setMessage("현재 비밀번호가 일치하지 않습니다.");
      } else if (error.response?.status === 401) {
        setMessage("인증이 필요합니다. 다시 로그인해주세요.");
      } else if (error.response?.data?.message) {
        setMessage(error.response.data.message);
      } else {
        setMessage("비밀번호 변경에 실패했습니다.");
      }
    } finally {
      setChangingPassword(false);
    }
  };

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

  // 프로필 초기 로딩 완료 시 상단 진행바 종료
  useEffect(() => {
    if (!loading) {
      endRouteProgress();
    }
  }, [loading]);

  if (loading) {
    return (
      <div className="h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>설정을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
      <Header onSidebarOpen={() => setSidebarOpen(true)} />
      <AppSidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
        onNavigate={handleNavigate}
      />
      <main className="flex flex-col items-center px-6 md:px-12 py-8 bg-transparent min-h-screen">
        <div className="w-full max-w-4xl pb-20">
          <h1 className="text-2xl md:text-3xl font-bold mb-4 tracking-tight text-white">
            개인 정보 설정 
          </h1>
          
          {message && (
            <div className={`mb-4 p-3 rounded-lg ${
              message.includes("성공") ? "bg-green-600" : "bg-red-600"
            }`}>
              {message}
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Profile Settings */}
            <div className="metric-card p-6 settings-section">
              <div className="flex items-center gap-3 mb-6">
                <User className="text-blue-400" size={24} />
                <h2 className="text-xl font-semibold text-white">프로필 설정</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">닉네임</label>
                  <input
                    type="text"
                    value={profileData.nickname}
                    onChange={(e) => handleProfileChange("nickname", e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="닉네임을 입력하세요"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">전화번호</label>
                  <input
                    type="text"
                    value={profileData.phone_number}
                    onChange={(e) => handleProfileChange("phone_number", e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="휴대폰 번호을 입력하세요"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">이메일</label>
                  <input
                    type="email"
                    value={profileData.email}
                    onChange={(e) => handleProfileChange("email", e.target.value)}
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
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      checked={notificationSettings.email_notifications_enabled}
                      onChange={(e) => handleSettingsChange("email_notifications_enabled", e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">SMS 알림</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      checked={notificationSettings.sms_notifications_enabled}
                      onChange={(e) => handleSettingsChange("sms_notifications_enabled", e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* API Keys Settings */}
            <div className="metric-card p-6 col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <Settings className="text-yellow-400" size={24} />
                <h2 className="text-xl font-semibold text-white">API 키 설정</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">한국투자증권 API 키</label>
                  <input
                    type="password"
                    value={profileData.korea_investment_app_key}
                    onChange={(e) => handleProfileChange("korea_investment_app_key", e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="한국투자증권 API 키"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">한국투자증권 Secret 키</label>
                  <input
                    type="password"
                    value={profileData.korea_investment_app_secret}
                    onChange={(e) => handleProfileChange("korea_investment_app_secret", e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="한국투자증권 Secret 키"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Alpha Vantage API 키</label>
                  <input
                    type="password"
                    value={profileData.alpha_vantage_key}
                    onChange={(e) => handleProfileChange("alpha_vantage_key", e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="Alpha Vantage API 키"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Polygon API 키</label>
                  <input
                    type="password"
                    value={profileData.polygon_key}
                    onChange={(e) => handleProfileChange("polygon_key", e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="Polygon API 키"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Finnhub API 키</label>
                  <input
                    type="password"
                    value={profileData.finnhub_key}
                    onChange={(e) => handleProfileChange("finnhub_key", e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="Finnhub API 키"
                  />
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
                {/* Password Change Section */}
                <div>
                  <div className="mb-4">
                    <span className="text-gray-300 font-medium">비밀번호 변경</span>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">현재 비밀번호</label>
                      <input
                        type="password"
                        value={passwordData.currentPassword}
                        onChange={(e) => handlePasswordChange("currentPassword", e.target.value)}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        placeholder="현재 비밀번호"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">새 비밀번호</label>
                      <input
                        type="password"
                        value={passwordData.newPassword}
                        onChange={(e) => handlePasswordChange("newPassword", e.target.value)}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        placeholder="새 비밀번호 (6자 이상)"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">새 비밀번호 확인</label>
                      <input
                        type="password"
                        value={passwordData.confirmPassword}
                        onChange={(e) => handlePasswordChange("confirmPassword", e.target.value)}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        placeholder="새 비밀번호 확인"
                      />
                    </div>
                    <button
                      onClick={handleChangePassword}
                      disabled={changingPassword || !passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword}
                      className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors"
                    >
                      {changingPassword ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white inline-block mr-2"></div>
                          변경 중...
                        </>
                      ) : (
                        "비밀번호 변경"
                      )}
                    </button>
                  </div>
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
              <button 
                onClick={handleSave}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg transition-colors"
              >
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