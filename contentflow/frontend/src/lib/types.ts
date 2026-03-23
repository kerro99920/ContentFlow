export interface ContentItem {
  id: string;
  platform: string;
  title: string | null;
  body: string | null;
  tags: string[] | null;
  metadata: Record<string, unknown> | null;
  brand_tone: string | null;
  status: string;
  created_at: string;
}

export interface ContentListResponse {
  items: ContentItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface GenerateResponse {
  task_id: string;
}

export interface TaskStatus {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  content_id: string | null;
  error_message: string | null;
}

export interface UserInfo {
  id: string;
  email: string;
  plan: string;
}

export interface UsageInfo {
  period: string;
  generation_count: number;
  quota: number;
}
