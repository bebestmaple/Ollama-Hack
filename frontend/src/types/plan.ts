// 计划创建请求
export interface PlanCreate {
  name: string;
  description?: string;
  rpm: number;
  rpd: number;
  is_default?: boolean;
}

// 计划响应
export interface PlanResponse extends PlanCreate {
  id: number;
}

// 计划更新请求
export interface PlanUpdate {
  name?: string;
  description?: string;
  rpm?: number;
  rpd?: number;
  is_default?: boolean;
}
