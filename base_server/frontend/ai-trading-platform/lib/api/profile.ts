import { apiClient } from './client';

export const profileService = {
  async getProfile() {
    return apiClient.post('/api/profile/get', {
      sequence: 0
    });
  },
  async setupProfile(data: any) {
    // 온보딩용 API - /api/account/profile/setup
    return apiClient.post('/api/account/profile/setup', {
      ...data,
      sequence: 0
    });
  },
  async updateProfile(data: any) {
    return apiClient.post('/api/profile/update-all', {
      ...data,
      sequence: 0
    });
  },
  async updateNotificationSettings(data: any) {
    return apiClient.post('/api/profile/update-notification', {
      ...data,
      sequence: 0
    });
  },
  async changePassword(currentPassword: string, newPassword: string, otpCode?: string) {
    return apiClient.post('/api/profile/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
      otp_code: otpCode || "",
      sequence: 0
    });
  },
};
