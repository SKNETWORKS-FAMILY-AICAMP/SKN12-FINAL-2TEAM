import { apiClient } from './client';

export const profileService = {
  async getProfile() {
    return apiClient.post('/api/account/profile/get', {});
  },
  async setupProfile(data: any) {
    return apiClient.post('/api/account/profile/setup', data);
  },
  async updateProfile(data: any) {
    return apiClient.post('/api/account/profile/update', data);
  },
}; 