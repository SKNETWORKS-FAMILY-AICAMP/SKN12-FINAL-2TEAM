"use client"

import { useState, useCallback } from "react";
import { profileService } from "@/lib/api/profile";

export interface ProfileData {
  nickname: string;
  email: string;
  phone_number: string;
  korea_investment_app_key: string;
  korea_investment_app_secret: string;
  alpha_vantage_key: string;
  polygon_key: string;
  finnhub_key: string;
}

export interface NotificationSettings {
  email_notifications_enabled: boolean;
  sms_notifications_enabled: boolean;
  push_notifications_enabled: boolean;
  price_alerts: boolean;
  news_alerts: boolean;
  portfolio_alerts: boolean;
  trade_alerts: boolean;
}

export interface PasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
  otpCode: string;
}

export function useProfile() {
  const [profileData, setProfileData] = useState<ProfileData>({
    nickname: "",
    email: "",
    phone_number: "",
    korea_investment_app_key: "",
    korea_investment_app_secret: "",
    alpha_vantage_key: "",
    polygon_key: "",
    finnhub_key: ""
  });

  const [originalProfileData, setOriginalProfileData] = useState<ProfileData>({
    nickname: "",
    email: "",
    phone_number: "",
    korea_investment_app_key: "",
    korea_investment_app_secret: "",
    alpha_vantage_key: "",
    polygon_key: "",
    finnhub_key: ""
  });

  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
    email_notifications_enabled: true,
    sms_notifications_enabled: true,
    push_notifications_enabled: true,
    price_alerts: true,
    news_alerts: true,
    portfolio_alerts: false,
    trade_alerts: true
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 프로필 데이터 로드
  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await profileService.getProfile() as any;
      console.log("[useProfile] Profile response:", response);

      if (response.errorCode === 0 && response.profile) {
        // profile이 문자열인 경우 파싱
        const profile = typeof response.profile === 'string' 
          ? JSON.parse(response.profile) 
          : response.profile;

        console.log("[useProfile] Raw profile data:", profile);

        const newProfileData: ProfileData = {
          nickname: profile.nickname ?? "",
          email: profile.email ?? "",
          phone_number: profile.phone_number ?? "",
          korea_investment_app_key: profile.korea_investment_app_key ?? "",
          korea_investment_app_secret: profile.korea_investment_app_secret ?? "",
          alpha_vantage_key: profile.alpha_vantage_key ?? "",
          polygon_key: profile.polygon_key ?? "",
          finnhub_key: profile.finnhub_key ?? ""
        };

        setProfileData(newProfileData);
        setOriginalProfileData(newProfileData);

        // 알림 설정도 profile에서 로드
        setNotificationSettings(prev => ({
          ...prev,
          email_notifications_enabled: profile.email_notifications_enabled ?? prev.email_notifications_enabled,
          sms_notifications_enabled: profile.sms_notifications_enabled ?? prev.sms_notifications_enabled,
          push_notifications_enabled: profile.push_notifications_enabled ?? prev.push_notifications_enabled,
          price_alerts: profile.price_alert_enabled ?? prev.price_alerts,
          news_alerts: profile.news_alert_enabled ?? prev.news_alerts,
          portfolio_alerts: profile.portfolio_alert_enabled ?? prev.portfolio_alerts,
          trade_alerts: profile.trade_alert_enabled ?? prev.trade_alerts
        }));
      } else {
        setError("프로필 데이터를 불러올 수 없습니다.");
      }
    } catch (error: any) {
      console.error("[useProfile] Failed to load profile:", error);
      setError("프로필 데이터 로드에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  // 프로필 데이터 업데이트
  const updateProfile = useCallback(async (newData: Partial<ProfileData>) => {
    try {
      setLoading(true);
      setError(null);

      // 백엔드 ProfileUpdateAllRequest 모델에 맞춰서 notificationSettings도 함께 전달
      const response = await profileService.updateAllProfile(newData, notificationSettings) as any;
      console.log("[useProfile] Update response:", response);

      if (response.errorCode === 0) {
        const updatedProfile = { ...profileData, ...newData };
        setProfileData(updatedProfile);
        setOriginalProfileData(updatedProfile);
        return { success: true };
      } else {
        setError("프로필 업데이트에 실패했습니다.");
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      console.error("[useProfile] Failed to update profile:", error);
      setError("프로필 업데이트에 실패했습니다.");
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, [profileData, notificationSettings]);

  // 알림 설정 업데이트
  const updateNotifications = useCallback(async (newSettings: Partial<NotificationSettings>) => {
    try {
      setLoading(true);
      setError(null);

      const notificationData = {
        email_notifications_enabled: newSettings.email_notifications_enabled ?? notificationSettings.email_notifications_enabled,
        sms_notifications_enabled: newSettings.sms_notifications_enabled ?? notificationSettings.sms_notifications_enabled,
        push_notifications_enabled: newSettings.push_notifications_enabled ?? notificationSettings.push_notifications_enabled,
        price_alert_enabled: newSettings.price_alerts ?? notificationSettings.price_alerts,
        news_alert_enabled: newSettings.news_alerts ?? notificationSettings.news_alerts,
        portfolio_alert_enabled: newSettings.portfolio_alerts ?? notificationSettings.portfolio_alerts,
        trade_alert_enabled: newSettings.trade_alerts ?? notificationSettings.trade_alerts
      };

      const response = await profileService.updateNotificationSettings(notificationData) as any;
      console.log("[useProfile] Notification update response:", response);

      if (response.errorCode === 0) {
        const updatedSettings = { ...notificationSettings, ...newSettings };
        setNotificationSettings(updatedSettings);
        return { success: true };
      } else {
        setError("알림 설정 업데이트에 실패했습니다.");
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      console.error("[useProfile] Failed to update notifications:", error);
      setError("알림 설정 업데이트에 실패했습니다.");
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, [notificationSettings]);

  // 비밀번호 변경
  const changePassword = useCallback(async (passwordData: PasswordData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await profileService.changePassword(passwordData) as any;
      console.log("[useProfile] Password change response:", response);

      if (response.errorCode === 0) {
        return { success: true };
      } else {
        setError("비밀번호 변경에 실패했습니다.");
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      console.error("[useProfile] Failed to change password:", error);
      setError("비밀번호 변경에 실패했습니다.");
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, []);

  // API 키 저장
  const saveApiKeys = useCallback(async (apiKeys: Partial<ProfileData>) => {
    try {
      setLoading(true);
      setError(null);

      const response = await profileService.saveApiKeys(apiKeys) as any;
      console.log("[useProfile] API keys save response:", response);

      if (response.errorCode === 0) {
        const updatedProfile = { ...profileData, ...apiKeys };
        setProfileData(updatedProfile);
        setOriginalProfileData(updatedProfile);
        return { success: true };
      } else {
        setError("API 키 저장에 실패했습니다.");
        return { success: false, error: response.message };
      }
    } catch (error: any) {
      console.error("[useProfile] Failed to save API keys:", error);
      setError("API 키 저장에 실패했습니다.");
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, [profileData]);

  // 에러 초기화
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // 프로필 데이터 변경 여부 확인
  const hasProfileChanges = useCallback(() => {
    return JSON.stringify(profileData) !== JSON.stringify(originalProfileData);
  }, [profileData, originalProfileData]);

  return {
    // 상태
    profileData,
    originalProfileData,
    notificationSettings,
    loading,
    error,
    
    // 액션
    loadProfile,
    updateProfile,
    updateNotifications,
    changePassword,
    saveApiKeys,
    clearError,
    hasProfileChanges,
    
    // 설정 함수
    setProfileData,
    setNotificationSettings
  };
} 