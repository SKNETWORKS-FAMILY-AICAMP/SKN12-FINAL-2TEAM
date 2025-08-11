import { apiClient } from "./client";

export type SetupProfilePayload = {
  investment_experience: "BEGINNER" | "INTERMEDIATE" | "EXPERT";
  risk_tolerance: "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE";
  investment_goal: "GROWTH" | "INCOME" | "PRESERVATION";
  monthly_budget: number;
};

export async function getProfile() {
  return apiClient.post('/profile/get', {
    // 필요한 데이터
  });
}

// 온보딩용 API - /api/account/profile/setup
export async function setupProfile(profileData: SetupProfilePayload) {
  console.log("[PROFILE API] 요청 URL: /api/account/profile/setup");
  console.log("[PROFILE API] 요청 데이터:", profileData);
  
  // 전체 API 경로 사용
  const res = await apiClient.post('/api/account/profile/setup', profileData);
  
  console.log("[PROFILE API] 응답:", res);
  return res; // res 자체를 반환 (apiClient에서 이미 data를 반환함)
}

export async function updateAllProfile(profileData: any) {
  return apiClient.post('/profile/update-all', profileData);
}

export async function updateNotificationSettings(settings: any) {
  return apiClient.post('/profile/update-notification', settings);
}

export async function changePassword(passwordData: any) {
  return apiClient.post('/profile/change-password', passwordData);
}
