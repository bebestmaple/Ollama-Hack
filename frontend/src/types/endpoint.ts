import {
  AIModelStatusEnum,
  EndpointStatusEnum,
  TaskStatusEnum,
} from "./common";

// 端点信息
export interface EndpointInfo {
  id?: number;
  url: string;
  name: string;
  created_at?: string;
}

// 端点性能信息
export interface EndpointPerformanceInfo {
  id?: number;
  status: EndpointStatusEnum;
  ollama_version?: string;
  created_at: string;
}

// 带 AI 模型数量的端点信息
export interface EndpointWithAIModelCount extends EndpointInfo {
  recent_performances: EndpointPerformanceInfo[];
  total_ai_model_count: number;
  avaliable_ai_model_count: number;
  task_status?: TaskStatusEnum;
}

// 端点 AI 模型信息
export interface EndpointAIModelInfo {
  id: number;
  name: string;
  tag: string;
  created_at: string;
  status: AIModelStatusEnum;
  token_per_second?: number;
  max_connection_time?: number;
}

// 带 AI 模型列表的端点信息
export interface EndpointWithAIModels extends EndpointInfo {
  recent_performances: EndpointPerformanceInfo[];
  ai_models: {
    items: EndpointAIModelInfo[];
    total?: number;
    page?: number;
    size?: number;
    pages?: number;
  };
}

// 端点创建请求
export interface EndpointCreate {
  url: string;
  name?: string;
}

// 端点更新请求
export interface EndpointUpdate {
  name?: string;
}

// 批量创建端点请求
export interface EndpointBatchCreate {
  endpoints: EndpointCreate[];
}

// 端点任务信息
export interface EndpointTaskInfo {
  id: number;
  endpoint_id: number;
  status: TaskStatusEnum;
  scheduled_at: string;
  last_tried?: string;
  created_at: string;
}
