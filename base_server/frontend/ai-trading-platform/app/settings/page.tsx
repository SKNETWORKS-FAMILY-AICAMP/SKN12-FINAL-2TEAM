"use client"

import React, { useState, useEffect } from "react";
import { Header } from "@/components/layout/header";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { useRouter } from "next/navigation";
import { useTutorial } from "@/hooks/use-tutorial"
import { TutorialOverlay } from "@/components/tutorial/tutorial-overlay"
import { Settings, User, Bell, Shield, CreditCard, LogOut } from "lucide-react";
import { profileService } from "@/lib/api/profile";
import { settingsService } from "@/lib/api/settings";

export default function SettingsPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  
  // Profile data
  const [profileData, setProfileData] = useState({
    nickname: "",
    email: "",
    phone_number: "",
    korea_investment_app_key: "",
    korea_investment_app_secret: "",
    alpha_vantage_key: "",
    polygon_key: "",
    finnhub_key: ""
  });
  
  // Original data for comparison (변경 감지용)
  const [originalProfileData, setOriginalProfileData] = useState({
    nickname: "",
    email: "",
    phone_number: "",
    korea_investment_app_key: "",
    korea_investment_app_secret: "",
    alpha_vantage_key: "",
    polygon_key: "",
    finnhub_key: ""
  });
  
  // Settings data (알림 설정만 사용)
  const [settingsData, setSettingsData] = useState({
    email_notifications_enabled: true,
    sms_notifications_enabled: true,
    push_notifications_enabled: true,
    price_alerts: true,
    news_alerts: true,
    portfolio_alerts: false,
    trade_alerts: true
  });

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
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load profile data (including notification settings)
      const profileResponse = await profileService.getProfile() as any;
      console.log("Profile response:", profileResponse); // 디버깅용
      
      if (profileResponse.errorCode === 0 && profileResponse.profile) {
        // profile이 문자열인 경우 파싱
        const profile = typeof profileResponse.profile === 'string' 
          ? JSON.parse(profileResponse.profile) 
          : profileResponse.profile;
        
        console.log("Raw profile data:", profile); // 디버깅용
        
        const newProfileData = {
          nickname: profile.nickname !== null && profile.nickname !== undefined ? profile.nickname : "",
          email: profile.email !== null && profile.email !== undefined ? profile.email : "",
          phone_number: profile.phone_number !== null && profile.phone_number !== undefined ? profile.phone_number : "",
          korea_investment_app_key: profile.korea_investment_app_key !== null && profile.korea_investment_app_key !== undefined ? profile.korea_investment_app_key : "",
          korea_investment_app_secret: profile.korea_investment_app_secret !== null && profile.korea_investment_app_secret !== undefined ? profile.korea_investment_app_secret : "",
          alpha_vantage_key: profile.alpha_vantage_key !== null && profile.alpha_vantage_key !== undefined ? profile.alpha_vantage_key : "",
          polygon_key: profile.polygon_key !== null && profile.polygon_key !== undefined ? profile.polygon_key : "",
          finnhub_key: profile.finnhub_key !== null && profile.finnhub_key !== undefined ? profile.finnhub_key : ""
        };
        
        console.log("Processed profile data:", newProfileData); // 디버깅용
        
        setProfileData(newProfileData);
        setOriginalProfileData(newProfileData); // 원본 데이터 저장
        
        // 알림 설정도 profile에서 로드
        setSettingsData(prev => ({
          ...prev,
          email_notifications_enabled: profile.email_notifications_enabled ?? prev.email_notifications_enabled,
          sms_notifications_enabled: profile.sms_notifications_enabled ?? prev.sms_notifications_enabled,
          push_notifications_enabled: profile.push_notifications_enabled ?? prev.push_notifications_enabled,
          price_alerts: profile.price_alert_enabled ?? true,
          news_alerts: profile.news_alert_enabled ?? true,
          portfolio_alerts: profile.portfolio_alert_enabled ?? false,
          trade_alerts: profile.trade_alert_enabled ?? true
        }));
      }
      
    } catch (error) {
      console.error("Failed to load data:", error);
      setMessage("데이터 로드에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage("");
      
      // 알림 설정만 별도로 업데이트
      const notificationData = {
        email_notifications_enabled: settingsData.email_notifications_enabled,
        sms_notifications_enabled: settingsData.sms_notifications_enabled,
        push_notifications_enabled: settingsData.push_notifications_enabled,
        price_alert_enabled: settingsData.price_alerts,
        news_alert_enabled: settingsData.news_alerts,
        portfolio_alert_enabled: settingsData.portfolio_alerts,
        trade_alert_enabled: settingsData.trade_alerts
      };

      // 알림 설정 업데이트
      await profileService.updateNotificationSettings(notificationData);
      
      // 프로필 데이터 변경사항이 있는지 확인
      const hasProfileChanges = 
        profileData.nickname !== originalProfileData.nickname ||
        profileData.email !== originalProfileData.email ||
        profileData.phone_number !== originalProfileData.phone_number ||
        profileData.korea_investment_app_key !== originalProfileData.korea_investment_app_key ||
        profileData.korea_investment_app_secret !== originalProfileData.korea_investment_app_secret ||
        profileData.alpha_vantage_key !== originalProfileData.alpha_vantage_key ||
        profileData.polygon_key !== originalProfileData.polygon_key ||
        profileData.finnhub_key !== originalProfileData.finnhub_key;
      
      // 프로필 데이터 변경사항이 있는 경우
      if (hasProfileChanges) {
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
        
        // 모든 필수 필드가 입력된 경우에만 업데이트
        const fullProfileData = {
          // 프로필 데이터 (현재 입력된 값 사용)
          nickname: profileData.nickname.trim(),
          email: profileData.email.trim(),
          phone_number: profileData.phone_number.trim(),
          korea_investment_app_key: profileData.korea_investment_app_key || "",
          korea_investment_app_secret: profileData.korea_investment_app_secret || "",
          alpha_vantage_key: profileData.alpha_vantage_key || "",
          polygon_key: profileData.polygon_key || "",
          finnhub_key: profileData.finnhub_key || "",
          
          // 필수 알림 설정 필드들 (현재 설정값 사용)
          email_notifications_enabled: settingsData.email_notifications_enabled,
          sms_notifications_enabled: settingsData.sms_notifications_enabled,
          push_notifications_enabled: settingsData.push_notifications_enabled,
          price_alert_enabled: settingsData.price_alerts,
          news_alert_enabled: settingsData.news_alerts,
          portfolio_alert_enabled: settingsData.portfolio_alerts,
          trade_alert_enabled: settingsData.trade_alerts,
          
          // 비밀번호 변경 (선택사항)
          current_password: null,
          new_password: null
        };
        
        try {
          await profileService.updateProfile(fullProfileData);
        } catch (profileError) {
          console.error("Profile update failed:", profileError);
          // 프로필 업데이트 실패해도 알림 설정은 성공했으므로 성공 메시지 표시
        }
      }
      
      setMessage("설정이 성공적으로 저장되었습니다.");
    } catch (error) {
      console.error("Failed to save settings:", error);
      setMessage("설정 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const handleProfileChange = (field: string, value: string) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSettingsChange = (field: string, value: any) => {
    setSettingsData(prev => ({
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
      const response = await profileService.changePassword(
        passwordData.currentPassword,
        passwordData.newPassword,
        passwordData.otpCode
      ) as any;

      // 응답이 문자열인 경우 파싱
      const responseData = typeof response === 'string' ? JSON.parse(response) : response;

      if (responseData.errorCode === 0) {
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
          setMessage(responseData.message || "비밀번호 변경에 실패했습니다.");
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
                      checked={settingsData.email_notifications_enabled}
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
                      checked={settingsData.sms_notifications_enabled}
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
                disabled={saving}
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    저장 중...
                  </>
                ) : (
                  <>
                    <LogOut size={16} />
                    변경 사항 적용
                  </>
                )}
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