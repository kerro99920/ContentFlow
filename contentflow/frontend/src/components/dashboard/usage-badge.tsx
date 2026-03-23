"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { UsageInfo } from "@/lib/types";

export function UsageBadge() {
  const [usage, setUsage] = useState<UsageInfo | null>(null);

  useEffect(() => {
    api.fetch<UsageInfo>("/api/user/usage").then(setUsage).catch(() => {});
  }, []);

  if (!usage) return null;

  return (
    <div className="mb-4 rounded-lg border p-3 text-sm">
      <p className="text-muted-foreground">本月用量</p>
      <p className="text-lg font-semibold">{usage.generation_count} / {usage.quota}</p>
    </div>
  );
}
