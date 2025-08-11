import { apiClient } from "./client";

export async function getProfile() {
  return apiClient.post('/profile/get', {
    // 필요한 데이터
  });
}

// 온보딩용 API - /account/profile/setup
export async function setupProfile(profileData: any) {
  return apiClient.post('/account/profile/setup', profileData);
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
