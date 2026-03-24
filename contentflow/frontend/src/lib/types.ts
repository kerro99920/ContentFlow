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

export interface BatchGenerateResponse {
  task_ids: Record<string, string>;
}

export interface BrandProfile {
  id: string;
  name: string;
  tone_description: string;
  system_prompt: string;
  industry_keywords: string[] | null;
  created_at: string;
}

export interface ScheduledTask {
  id: string;
  name: string;
  cron_expression: string;
  source_material: string;
  platforms: string[];
  brand_tone: string;
  is_active: boolean;
  last_run_at: string | null;
  created_at: string;
}

export interface CalendarDay {
  date: string;
  items: ContentItem[];
}

export interface CalendarResponse {
  month: string;
  days: CalendarDay[];
}

export const PLATFORMS = [
  { value: "xiaohongshu", label: "小红书" },
  { value: "douyin", label: "抖音" },
  { value: "wechat", label: "公众号" },
  { value: "blog", label: "博客" },
  { value: "twitter", label: "Twitter/X" },
  { value: "bilibili", label: "B站" },
] as const;
