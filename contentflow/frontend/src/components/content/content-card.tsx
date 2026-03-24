"use client";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CopyButton } from "./copy-button";
import { EditModal } from "./edit-modal";
import { api } from "@/lib/api";
import type { ContentItem } from "@/lib/types";

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  approved: "已审核",
  published: "已发布",
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
        </div>
        {editing && (
          <EditModal
            content={content}
            onSaved={(updated) => { setContent(updated); setEditing(false); }}
            onCancel={() => setEditing(false)}
          />
        )}
      </CardContent>
    </Card>
  );
}
