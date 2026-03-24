"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { ContentItem } from "@/lib/types";

interface Props {
  content: ContentItem;
  onSaved: (updated: ContentItem) => void;
  onCancel: () => void;
}

export function EditModal({ content, onSaved, onCancel }: Props) {
  const [title, setTitle] = useState(content.title || "");
  const [body, setBody] = useState(content.body || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.fetch<ContentItem>(`/api/content/${content.id}`, {
        method: "PUT",
        body: JSON.stringify({ title, body }),
      });
      onSaved(updated);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="mt-4">
      <CardHeader><CardTitle>编辑内容</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><Label>标题</Label><Input value={title} onChange={(e) => setTitle(e.target.value)} /></div>
        <div><Label>正文</Label><Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={10} /></div>
        <div className="flex gap-2">
          <Button onClick={handleSave} disabled={saving}>{saving ? "保存中..." : "保存"}</Button>
          <Button variant="outline" onClick={onCancel}>取消</Button>
        </div>
      </CardContent>
    </Card>
  );
}
