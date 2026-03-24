"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { GenerateResponse, TaskStatus, ContentItem, BatchGenerateResponse, BrandProfile } from "@/lib/types";
import { PLATFORMS } from "@/lib/types";

const tones = [
  { value: "professional", label: "专业严谨" },
  { value: "casual", label: "轻松活泼" },
  { value: "seeding", label: "种草安利" },
];

interface Props {
  onGenerated: (contents: ContentItem[]) => void;
}

export function GenerateForm({ onGenerated }: Props) {
  const [material, setMaterial] = useState("");
  const [tone, setTone] = useState("casual");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["xiaohongshu"]);
  const [brandProfiles, setBrandProfiles] = useState<BrandProfile[]>([]);
  const [brandProfileId, setBrandProfileId] = useState<string>("__custom__");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.fetch<BrandProfile[]>("/api/brand-profiles")
      .then((profiles) => setBrandProfiles(profiles))
      .catch(() => {});
  }, []);

  const togglePlatform = (value: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value]
    );
  };

  const pollTask = async (taskId: string): Promise<ContentItem | null> => {
    let status: TaskStatus;
    do {
      await new Promise((r) => setTimeout(r, 1500));
      status = await api.fetch<TaskStatus>(`/api/content/tasks/${taskId}`);
    } while (status.status === "pending" || status.status === "running");

    if (status.status === "completed" && status.content_id) {
      return api.fetch<ContentItem>(`/api/content/${status.content_id}`);
    }
    return null;
  };

  const handleGenerate = async () => {
    if (!material.trim() || selectedPlatforms.length === 0) return;
    setLoading(true);
    setError("");

    try {
      const brandTone = brandProfileId !== "__custom__"
        ? (brandProfiles.find((p) => p.id === brandProfileId)?.tone_description ?? tone)
        : tone;

      if (selectedPlatforms.length === 1) {
        const { task_id } = await api.fetch<GenerateResponse>("/api/content/generate", {
          method: "POST",
          body: JSON.stringify({
            source_material: material,
            platform: selectedPlatforms[0],
            brand_tone: brandTone,
          }),
        });
        const content = await pollTask(task_id);
        if (content) {
          onGenerated([content]);
          setMaterial("");
        } else {
          setError("生成失败，请重试");
        }
      } else {
        const { task_ids } = await api.fetch<BatchGenerateResponse>("/api/content/generate-batch", {
          method: "POST",
          body: JSON.stringify({
            source_material: material,
            platforms: selectedPlatforms,
            brand_tone: brandTone,
          }),
        });

        const results = await Promise.all(
          Object.values(task_ids).map((id) => pollTask(id))
        );
        const contents = results.filter((c): c is ContentItem => c !== null);
        if (contents.length > 0) {
          onGenerated(contents);
          setMaterial("");
        } else {
          setError("生成失败，请重试");
        }
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
        <Label>发布平台</Label>
        <div className="mt-2 flex flex-wrap gap-3">
          {PLATFORMS.map((p) => (
            <label key={p.value} className="flex cursor-pointer items-center gap-1.5 text-sm">
              <input
                type="checkbox"
                className="rounded border-gray-300"
                checked={selectedPlatforms.includes(p.value)}
                onChange={() => togglePlatform(p.value)}
              />
              {p.label}
            </label>
          ))}
        </div>
      </div>
      <div>
        <Label>品牌模板</Label>
        <Select value={brandProfileId} onValueChange={(v) => { if (v !== null) setBrandProfileId(v); }}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__custom__">自定义模板</SelectItem>
            {brandProfiles.map((p) => (
              <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {brandProfileId === "__custom__" && (
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
      )}
      {error && <p className="text-sm text-red-500">{error}</p>}
      <Button
        onClick={handleGenerate}
        disabled={loading || !material.trim() || selectedPlatforms.length === 0}
      >
        {loading ? "AI 生成中..." : "生成内容"}
      </Button>
    </div>
  );
}
