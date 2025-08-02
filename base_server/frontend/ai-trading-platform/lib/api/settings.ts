import { apiClient } from './client';

export interface UserSettings {
  // 프로필 설정
  investment_experience: string;
  risk_tolerance: string;
  investment_goal: string;
  monthly_budget: number;
  
  // 알림 설정
  price_alerts: boolean;
  news_alerts: boolean;
  portfolio_alerts: boolean;
  trade_alerts: boolean;
  email_notifications_enabled: boolean;
  sms_notifications_enabled: boolean;
  push_notifications_enabled: boolean;
  
  // 보안 설정
  otp_enabled: boolean;
  biometric_enabled: boolean;
  session_timeout: number;
  login_alerts: boolean;
  
  // 화면 설정
  theme: string;
  language: string;
  currency: string;
  chart_style: string;
  
  // 거래 설정
  auto_trading_enabled: boolean;
  max_position_size: number;
  stop_loss_default: number;
  take_profit_default: number;
}

export interface NotificationSettings {
  price_change_threshold: number;
  news_keywords: string[];
  portfolio_rebalance_alerts: boolean;
  daily_summary: boolean;
  weekly_report: boolean;
}

export interface SecuritySettings {
  password_change_required: boolean;
  last_password_change: string;
  failed_login_attempts: number;
  device_trust_enabled: boolean;
  ip_whitelist: string[];
}

export const settingsService = {
  // 설정 조회
  async getSettings(section: string = "ALL") {
    return apiClient.post('/api/settings/get', {
      section,
      sequence: 0
    });
  },

  // 설정 업데이트
  async updateSettings(section: string, settings: any) {
    return apiClient.post('/api/settings/update', {
      section,
      settings,
      sequence: 0
    });
  },

  // 설정 초기화
  async resetSettings(section: string, confirm: boolean = false) {
    return apiClient.post('/api/settings/reset', {
      section,
      confirm,
      sequence: 0
    });
  },

  // OTP 활성화/비활성화
  async toggleOTP(enable: boolean, currentPassword: string, otpCode?: string) {
    return apiClient.post('/api/settings/otp/toggle', {
      enable,
      current_password: currentPassword,
      otp_code: otpCode || "",
      sequence: 0
    });
  },

  // 비밀번호 변경
  async changePassword(currentPassword: string, newPassword: string, otpCode?: string) {
    return apiClient.post('/api/settings/password/change', {
      current_password: currentPassword,
      new_password: newPassword,
      otp_code: otpCode || "",
      sequence: 0
    });
  },

  // 현재 비밀번호 확인
  async verifyPassword(currentPassword: string) {
    return apiClient.post('/api/settings/password/verify', {
      current_password: currentPassword,
      sequence: 0
    });
  },

  // 데이터 내보내기
  async exportData(dataTypes: string[] = ["PORTFOLIO", "TRANSACTIONS", "SETTINGS"], format: string = "JSON") {
    return apiClient.post('/api/settings/export-data', {
      data_types: dataTypes,
      format,
      sequence: 0
    });
  }
}; 