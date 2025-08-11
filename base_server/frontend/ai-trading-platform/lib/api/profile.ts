import { apiClient } from "./client";

export type SetupProfilePayload = {
  investment_experience: "BEGINNER" | "INTERMEDIATE" | "EXPERT";
  risk_tolerance: "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE";
  investment_goal: "GROWTH" | "INCOME" | "PRESERVATION";
  monthly_budget: number;
};

// Profile API - 백엔드 profile.py 라우터와 연결
export async function getProfile() {
  return apiClient.post('/api/profile/get', {
    // 필요한 데이터
  });
}

// 온보딩용 API - /api/account/profile/setup (기존 유지)
export async function setupProfile(profileData: SetupProfilePayload) {
  console.log("[PROFILE API] 요청 URL: /api/account/profile/setup");
  console.log("[PROFILE API] 요청 데이터:", profileData);
  
  // 전체 API 경로 사용
  const res = await apiClient.post('/api/account/profile/setup', profileData);
  
  console.log("[PROFILE API] 응답:", res);
  return res; // res 자체를 반환 (apiClient에서 이미 data를 반환함)
}

// Profile 업데이트 - 백엔드 ProfileUpdateAllRequest 모델에 맞춤
export async function updateAllProfile(profileData: any, notificationSettings: any) {
  // 백엔드 ProfileUpdateAllRequest 모델에 맞는 데이터 구조로 변환
  const requestData = {
    // 기본 프로필
    nickname: profileData.nickname || "",
    email: profileData.email || "",
    phone_number: profileData.phone_number || "",
    
    // 알림 설정
    email_notifications_enabled: notificationSettings.email_notifications_enabled || false,
    sms_notifications_enabled: notificationSettings.sms_notifications_enabled || false,
    push_notifications_enabled: notificationSettings.push_notifications_enabled || false,
    price_alert_enabled: notificationSettings.price_alerts || false,
    news_alert_enabled: notificationSettings.news_alerts || false,
    portfolio_alert_enabled: notificationSettings.portfolio_alerts || false,
    trade_alert_enabled: notificationSettings.trade_alerts || false,
    
    // 비밀번호 변경 (선택사항)
    current_password: null,
    new_password: null,
    
    // API 키 (선택사항)
    korea_investment_app_key: profileData.korea_investment_app_key || "",
    korea_investment_app_secret: profileData.korea_investment_app_secret || "",
    alpha_vantage_key: profileData.alpha_vantage_key || "",
    polygon_key: profileData.polygon_key || "",
    finnhub_key: profileData.finnhub_key || ""
  };
  
  console.log("[PROFILE API] updateAllProfile 요청 데이터:", requestData);
  
  return apiClient.post('/api/profile/update-all', requestData);
}

// 알림 설정 업데이트 - 백엔드 profile.py와 연결
export async function updateNotificationSettings(settings: any) {
  return apiClient.post('/api/profile/update-notification', settings);
}

// 비밀번호 변경 - 백엔드 profile.py와 연결
export async function changePassword(passwordData: any) {
  return apiClient.post('/api/profile/change-password', passwordData);
}

// 기본 프로필 업데이트 - 백엔드 profile.py와 연결
export async function updateBasicProfile(basicData: any) {
  return apiClient.post('/api/profile/update-basic', basicData);
}

// API 키 저장 - 백엔드 profile.py와 연결
export async function saveApiKeys(apiKeys: any) {
  return apiClient.post('/api/profile/api-keys/save', apiKeys);
}

// API 키 조회 - 백엔드 profile.py와 연결
export async function getApiKeys() {
  return apiClient.post('/api/profile/api-keys/get', {});
}

// profileService 객체로 export (settings 페이지 호환성)
export const profileService = {
  getProfile,
  setupProfile,
  updateAllProfile,
  updateNotificationSettings,
  changePassword,
  updateBasicProfile,
  saveApiKeys,
  getApiKeys
};
