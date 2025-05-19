import { AIModelStatusEnum } from "./common";

// AI 模型性能信息
export interface AIModelPerformance {
  id: number;
  status: AIModelStatusEnum;
  token_per_second?: number;
  connection_time?: number;
  total_time?: number;
  created_at: string;
}

// 带端点信息的模型信息
export interface ModelFromEndpointInfo {
  id: number;
  url: string;
  name: string;
  created_at: string;
  status: AIModelStatusEnum;
  token_per_second?: number;
  max_connection_time?: number;
  model_performances: AIModelPerformance[];
}

// 带端点数量的 AI 模型信息
export interface AIModelInfoWithEndpointCount {
  id?: number;
  name: string;
  tag: string;
  created_at: string;
  total_endpoint_count: number;
  avaliable_endpoint_count: number;
}

// 带端点的 AI 模型详情
export interface AIModelInfoWithEndpoint {
  id?: number;
  name: string;
  tag: string;
  created_at: string;
  total_endpoint_count: number;
  avaliable_endpoint_count: number;
  endpoints: {
    items: ModelFromEndpointInfo[];
    total?: number;
    page?: number;
    size?: number;
    pages?: number;
  };
}
