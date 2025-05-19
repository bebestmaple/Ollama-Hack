// 用户认证请求
export interface UserAuth {
  username: string;
  password: string;
}

// Token 响应
export interface Token {
  access_token: string;
  token_type: string;
}

// 用户信息
export interface UserInfo {
  id: number;
  username: string;
  is_admin: boolean;
  plan_id?: number;
  plan_name?: string;
}

// 用户更新请求
export interface UserUpdate {
  username?: string;
  is_admin?: boolean;
  password?: string;
  plan_id?: number;
}

// 密码修改请求
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}
