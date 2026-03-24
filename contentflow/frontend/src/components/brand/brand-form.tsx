"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { BrandProfile } from "@/lib/types";
import { toast } from "sonner";

interface Props {
  onCreated: () => void;
}

export function BrandForm({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [toneDescription, setToneDescription] = useState("");
  const [keywords, setKeywords] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!name.trim() || !toneDescription.trim()) return;
    setLoading(true);
    setError("");
    try {
      const payload: Record<string, unknown> = {
        name,
        tone_description: toneDescription,
      };
      if (keywords.trim()) {
        payload.industry_keywords = keywords.split(",").map((k) => k.trim()).filter(Boolean);
      }
      await api.fetch<BrandProfile>("/api/brand-profiles", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setName("");
      setToneDescription("");
      setKeywords("");
      toast.success("品牌模板已创建");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader><CardTitle>新建品牌模板</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>模板名称</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="例：科技品牌" />
        </div>
        <div>
          <Label>调性描述</Label>
          <Textarea
            value={toneDescription}
            onChange={(e) => setToneDescription(e.target.value)}
            placeholder="描述品牌的语言风格和调性..."
            rows={3}
          />
        </div>
        <div>
          <Label>行业关键词（逗号分隔）</Label>
          <Input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="科技, 创新, 智能" />
        </div>
        {error && <p className="text-sm text-red-500">{error}</p>}
        <Button onClick={handleSubmit} disabled={loading || !name.trim() || !toneDescription.trim()}>
          {loading ? "AI 生成中..." : "创建模板"}
        </Button>
      </CardContent>
    </Card>
  );
}
