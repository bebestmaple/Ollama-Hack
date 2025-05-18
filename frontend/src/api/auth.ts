import apiClient, { buildQueryString } from "./client";

import {
  ChangePasswordRequest,
  PageResponse,
  QueryParams,
  Token,
  UserAuth,
  UserInfo,
  UserUpdate,
} from "@/types";

export const authApi = {
  // 初始化第一个用户
  initUser: (data: UserAuth) => {
    return apiClient.post<void>("/api/v2/user/init", data);
  },

  // 用户登录
  login: (username: string, password: string) => {
    const formData = new URLSearchParams();

    formData.append("username", username);
    formData.append("password", password);

    return apiClient.post<Token>("/api/v2/user/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
  },

  // 获取当前用户信息
  getCurrentUser: () => {
    return apiClient.get<UserInfo>("/api/v2/user/me");
  },

  // 修改当前用户密码
  changePassword: (data: ChangePasswordRequest) => {
    return apiClient.patch<UserInfo>(
      `/api/v2/user/me/change-password?old_password=${data.old_password}&new_password=${data.new_password}`,
    );
  },

  // 创建新用户 (需要管理员权限)
  createUser: (data: UserAuth) => {
    return apiClient.post<UserInfo>("/api/v2/user/", data);
  },

  // 获取所有用户 (需要管理员权限)
  getUsers: (params: QueryParams = {}) => {
    const queryString = buildQueryString({
      page: params.page || 1,
      size: params.size || 50,
      search: params.search,
      order_by: params.order_by,
      order: params.order,
    });

    return apiClient.get<PageResponse<UserInfo>>(`/api/v2/user/${queryString}`);
  },

  // 根据 ID 获取用户 (需要管理员权限)
  getUserById: (userId: number) => {
    return apiClient.get<UserInfo>(`/api/v2/user/${userId}`);
  },

  // 更新用户 (需要管理员权限)
  updateUser: (userId: number, data: UserUpdate) => {
    return apiClient.patch<UserInfo>(`/api/v2/user/${userId}`, data);
  },

  // 删除用户 (需要管理员权限)
  deleteUser: (userId: number) => {
    return apiClient.delete<void>(`/api/v2/user/${userId}`);
  },
};

export default authApi;
