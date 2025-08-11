import { apiClient } from "./client";

export interface Settings {
  // 설정 인터페이스 정의
  [key: string]: any;
}

export interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  sms_notifications: boolean;
  trading_alerts: boolean;
  market_updates: boolean;
  portfolio_summary: boolean;
}

export interface SecuritySettings {
  two_factor_auth: boolean;
  login_alerts: boolean;
  session_timeout: number;
  ip_whitelist: string[];
}

export interface TradingSettings {
  auto_trading: boolean;
  risk_tolerance: string;
  max_position_size: number;
  stop_loss_percentage: number;
  take_profit_percentage: number;
}

export interface PrivacySettings {
  data_sharing: boolean;
  analytics_tracking: boolean;
  marketing_emails: boolean;
  third_party_access: boolean;
}

export async function getSettings(): Promise<Settings> {
  return apiClient.post('/settings/get', {
    // 필요한 데이터
  });
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  return apiClient.post('/settings/update', {
    ...settings
  });
}

export async function resetSettings(): Promise<void> {
  return apiClient.post('/settings/reset', {
    // 리셋 확인 데이터
  });
}

export async function toggleOTP(): Promise<{ two_factor_auth: boolean }> {
  return apiClient.post('/settings/otp/toggle', {
    // OTP 토글 데이터
  });
}

export async function changePassword(
  currentPassword: string, 
  newPassword: string, 
  otpCode?: string
): Promise<{ success: boolean }> {
  return apiClient.post('/settings/password/change', {
    current_password: currentPassword,
    new_password: newPassword,
    otp_code: otpCode || ""
  });
}

export async function verifyPassword(password: string): Promise<{ valid: boolean }> {
  return apiClient.post('/settings/password/verify', {
    password
  });
}

export async function exportData(): Promise<{ download_url: string }> {
  return apiClient.post('/settings/export-data', {
    // 내보내기 옵션
  });
} 