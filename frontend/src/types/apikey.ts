// API 密钥创建请求
export interface ApiKeyCreate {
  name: string;
}

// API 密钥信息
export interface ApiKeyInfo {
  id: number;
  name: string;
  created_at: string;
  last_used_at?: string;
  user_id?: number;
  user_name?: string;
}

// API 密钥响应（包含密钥值）
export interface ApiKeyResponse extends ApiKeyInfo {
  key: string;
}

// API 密钥使用统计
export interface ApiKeyUsageStats {
  total_requests: number;
  last_30_days_requests: number;
  requests_today: number;
  successful_requests: number;
  failed_requests: number;
  requests_per_day: {
    date: string;
    count: number;
  }[];
}
