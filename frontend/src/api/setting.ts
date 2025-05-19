import apiClient from "./client";

import { SystemSettingKey, SystemSettings } from "@/types";

export const settingApi = {
  // 获取所有设置
  getSettings: () => {
    return apiClient.get<Record<SystemSettingKey, string>>(`/api/v2/setting/`);
  },

  // 根据 key 获取设置
  getSettingByKey: (key: SystemSettingKey) => {
    return apiClient.get<SystemSettings>(`/api/v2/setting/${key}`);
  },

  // 更新设置
  updateSetting: (key: SystemSettingKey, value: string) => {
    return apiClient.patch<SystemSettings>(
      `/api/v2/setting/${key}?value=${value}`,
    );
  },
};

export default settingApi;
