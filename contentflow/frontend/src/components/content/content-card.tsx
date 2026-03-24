"use client";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CopyButton } from "./copy-button";
import { EditModal } from "./edit-modal";
import { api } from "@/lib/api";
import type { ContentItem } from "@/lib/types";
import { toast } from "sonner";

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  approved: "已审核",
  published: "已发布",
};

const PUBLISH_PLATFORMS: Record<string, string> = {
  twitter: "Twitter/X",
  xiaohongshu: "小红书",
  bilibili: "B站",
};

const STATUS_VARIANTS: Record<string, "secondary" | "default" | "outline"> = {
  draft: "secondary",
  approved: "default",
  published: "outline",
};

export function ContentCard({ content: initialContent }: { content: ContentItem }) {
  const [content, setContent] = useState(initialContent);
  const [editing, setEditing] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const handlePublish = async (platform: string) => {
    setPublishing(true);
    try {
      const result = await api.fetch<{ success: boolean; message: string }>("/api/publish", {
        method: "POST",
        body: JSON.stringify({ content_id: content.id, platform }),
      });
      if (result.success) {
        toast.success(result.message);
        setContent({ ...content, status: "published" });
      } else {
        toast.error(result.message);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "发布失败");
    } finally {
      setPublishing(false);
    }
  };

  const changeStatus = async (status: string) => {
    setStatusLoading(true);
    try {
      const updated = await api.fetch<ContentItem>(`/api/content/${content.id}`, {
        method: "PUT",
        body: JSON.stringify({ status }),
      });
      setContent(updated);
    } finally {
      setStatusLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{content.title || "无标题"}</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_VARIANTS[content.status] ?? "secondary"}>
              {STATUS_LABELS[content.status] ?? content.status}
            </Badge>
            <Badge variant="secondary">{content.platform}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="whitespace-pre-wrap text-sm">{content.body}</p>
        {content.tags && (
          <div className="flex flex-wrap gap-1">
            {content.tags.map((tag) => (
              <Badge key={tag} variant="outline">#{tag}</Badge>
            ))}
          </div>
        )}
        {content.metadata?.cover_text != null && (
          <p className="text-sm text-muted-foreground">封面建议：{String(content.metadata.cover_text)}</p>
        )}
        <div className="flex flex-wrap gap-2 pt-1">
          <CopyButton content={content} />
          <Button variant="outline" size="sm" onClick={() => setEditing((e) => !e)}>
            {editing ? "取消编辑" : "编辑"}
          </Button>
          {content.status === "draft" && (
            <Button variant="outline" size="sm" disabled={statusLoading} onClick={() => changeStatus("approved")}>
              标记已审核
            </Button>
          )}
          {content.status === "approved" && (
            <Button variant="outline" size="sm" disabled={statusLoading} onClick={() => changeStatus("published")}>
              标记已发布
            </Button>
          )}
          {content.platform in PUBLISH_PLATFORMS && content.status !== "published" && (
            <Button
              size="sm"
              disabled={publishing}
              onClick={() => handlePublish(content.platform)}
            >
              {publishing ? "发布中..." : `发布到${PUBLISH_PLATFORMS[content.platform] || content.platform}`}
            </Button>
          )}
        </div>
        {editing && (
          <EditModal
            content={content}
            onSaved={(updated) => { setContent(updated); setEditing(false); toast.success("内容已更新"); }}
            onCancel={() => setEditing(false)}
          />
        )}
      </CardContent>
    </Card>
  );
}
