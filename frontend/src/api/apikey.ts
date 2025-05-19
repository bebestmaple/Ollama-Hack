import apiClient, { buildQueryString } from "./client";

import {
  ApiKeyCreate,
  ApiKeyInfo,
  ApiKeyResponse,
  ApiKeyUsageStats,
  PageResponse,
  QueryParams,
} from "@/types";

export const apiKeyApi = {
  // 获取当前用户的所有 API 密钥
  getApiKeys: (params: QueryParams = {}) => {
    const queryString = buildQueryString({
      page: params.page || 1,
      size: params.size || 50,
      search: params.search,
      order_by: params.order_by,
      order: params.order,
    });

    return apiClient.get<PageResponse<ApiKeyInfo>>(
      `/api/v2/apikey/${queryString}`,
    );
  },

  // 创建新的 API 密钥
  createApiKey: (data: ApiKeyCreate) => {
    return apiClient.post<ApiKeyResponse>("/api/v2/apikey/", data);
  },

  // 删除 API 密钥
  deleteApiKey: (apiKeyId: number) => {
    return apiClient.delete<void>(`/api/v2/apikey/${apiKeyId}`);
  },

  // 获取 API 密钥使用统计
  getApiKeyStats: (apiKeyId: number) => {
    return apiClient.get<ApiKeyUsageStats>(`/api/v2/apikey/${apiKeyId}/stats`);
  },
};

export default apiKeyApi;
