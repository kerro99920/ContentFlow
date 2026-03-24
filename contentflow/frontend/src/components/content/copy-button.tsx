"use client";
import { Button } from "@/components/ui/button";
import type { ContentItem } from "@/lib/types";
import { useState } from "react";
import { toast } from "sonner";

function formatForCopy(content: ContentItem): string {
  if (content.platform === "xiaohongshu") {
    const tags = content.tags?.map((t) => `#${t}`).join(" ") || "";
    return `${content.title || ""}\n\n${content.body || ""}\n\n${tags}`;
  }
  if (content.platform === "douyin") {
    const meta = content.metadata;
    const subtitle = meta && typeof meta === "object" ? String(meta.subtitle_text || "") : "";
    return subtitle || content.body || "";
  }
  return `${content.title || ""}\n\n${content.body || ""}`;
}

export function CopyButton({ content }: { content: ContentItem }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(formatForCopy(content));
    setCopied(true);
    toast.success("已复制到剪贴板");
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <Button variant="outline" size="sm" onClick={handleCopy}>
      {copied ? "已复制" : "复制"}
    </Button>
  );
}
