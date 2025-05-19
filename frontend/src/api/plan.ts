import apiClient, { buildQueryString } from "./client";

import {
  PageResponse,
  PlanCreate,
  PlanResponse,
  PlanUpdate,
  QueryParams,
} from "@/types";

export const planApi = {
  // 获取所有计划
  getPlans: (params: QueryParams = {}) => {
    const queryString = buildQueryString({
      page: params.page || 1,
      size: params.size || 50,
      search: params.search,
      order_by: params.order_by,
      order: params.order,
    });

    return apiClient.get<PageResponse<PlanResponse>>(
      `/api/v2/plan/${queryString}`,
    );
  },

  // 创建新计划
  createPlan: (data: PlanCreate) => {
    return apiClient.post<PlanResponse>("/api/v2/plan/", data);
  },

  // 根据 ID 获取计划
  getPlanById: (planId: number) => {
    return apiClient.get<PlanResponse>(`/api/v2/plan/${planId}`);
  },

  // 获取当前用户的计划
  getCurrentUserPlan: () => {
    return apiClient.get<PlanResponse>("/api/v2/plan/me");
  },

  // 更新计划
  updatePlan: (planId: number, data: PlanUpdate) => {
    return apiClient.patch<PlanResponse>(`/api/v2/plan/${planId}`, data);
  },

  // 删除计划
  deletePlan: (planId: number) => {
    return apiClient.delete<void>(`/api/v2/plan/${planId}`);
  },
};

export default planApi;
