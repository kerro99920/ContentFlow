"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { GenerateResponse, TaskStatus, ContentItem } from "@/lib/types";

const tones = [
  { value: "professional", label: "专业严谨" },
  { value: "casual", label: "轻松活泼" },
  { value: "seeding", label: "种草安利" },
];

interface Props {
  onGenerated: (content: ContentItem) => void;
}

export function GenerateForm({ onGenerated }: Props) {
  const [material, setMaterial] = useState("");
  const [tone, setTone] = useState("casual");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!material.trim()) return;
    setLoading(true);
    setError("");

    try {
      const { task_id } = await api.fetch<GenerateResponse>("/api/content/generate", {
        method: "POST",
        body: JSON.stringify({
          source_material: material,
          platform: "xiaohongshu",
          brand_tone: tone,
        }),
      });

      let status: TaskStatus;
      do {
        await new Promise((r) => setTimeout(r, 1500));
        status = await api.fetch<TaskStatus>(`/api/content/tasks/${task_id}`);
      } while (status.status === "pending" || status.status === "running");

      if (status.status === "completed" && status.content_id) {
        const content = await api.fetch<ContentItem>(`/api/content/${status.content_id}`);
        onGenerated(content);
        setMaterial("");
      } else {
        setError(status.error_message || "生成失败，请重试");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>素材内容</Label>
        <Textarea
          value={material}
          onChange={(e) => setMaterial(e.target.value)}
          placeholder="输入你的素材：产品描述、灵感、主题..."
          rows={6}
        />
      </div>
      <div>
        <Label>品牌调性</Label>
        <Select value={tone} onValueChange={(v) => { if (v !== null) setTone(v); }}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {tones.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
      <Button onClick={handleGenerate} disabled={loading || !material.trim()}>
        {loading ? "AI 生成中..." : "生成小红书内容"}
      </Button>
    </div>
  );
}
