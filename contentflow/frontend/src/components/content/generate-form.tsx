"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { GenerateResponse, TaskStatus, ContentItem, BatchGenerateResponse, BrandProfile } from "@/lib/types";
import { PLATFORMS } from "@/lib/types";
import { toast } from "sonner";

const tones = [
  { value: "professional", label: "专业严谨" },
  { value: "casual", label: "轻松活泼" },
  { value: "seeding", label: "种草安利" },
];

interface Props {
  onGenerated: (contents: ContentItem[]) => void;
}

interface TrendItem {
  title: string;
  source: string;
  hot_score: number;
}

const SOURCE_LABELS: Record<string, string> = {
  toutiao: "头条", baidu: "百度", zhihu: "知乎",
};

export function GenerateForm({ onGenerated }: Props) {
  const [material, setMaterial] = useState("");
  const [tone, setTone] = useState("casual");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["xiaohongshu"]);
  const [brandProfiles, setBrandProfiles] = useState<BrandProfile[]>([]);
  const [brandProfileId, setBrandProfileId] = useState<string>("__custom__");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [showTrends, setShowTrends] = useState(false);

  useEffect(() => {
    api.fetch<BrandProfile[]>("/api/brand-profiles")
      .then((profiles) => setBrandProfiles(profiles))
      .catch(() => {});
  }, []);

  const loadTrends = async () => {
    if (trends.length > 0) {
      setShowTrends(!showTrends);
      return;
    }
    setTrendsLoading(true);
    try {
      const data = await api.fetch<TrendItem[]>("/api/content/trends");
      setTrends(data);
      setShowTrends(true);
    } catch {
      setError("获取热点失败");
    } finally {
      setTrendsLoading(false);
    }
  };

  const togglePlatform = (value: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value]
    );
  };

  const pollTask = async (taskId: string): Promise<ContentItem | null> => {
    let status: TaskStatus;
    let attempts = 0;
    const maxAttempts = 40;
    do {
      await new Promise((r) => setTimeout(r, 1500));
      status = await api.fetch<TaskStatus>(`/api/content/tasks/${taskId}`);
      attempts++;
      if (attempts >= maxAttempts) {
        return null;
      }
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
          toast.success("内容生成完成");
        } else {
          const msg = "生成失败，请重试";
          setError(msg);
          toast.error(msg);
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
          toast.success("内容生成完成");
        } else {
          const msg = "生成失败，请重试";
          setError(msg);
          toast.error(msg);
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "请求失败";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <Label>素材内容</Label>
          <Button variant="outline" size="sm" onClick={loadTrends} disabled={trendsLoading}>
            {trendsLoading ? "加载中..." : showTrends ? "收起热点" : "选择热点话题"}
          </Button>
        </div>
        {showTrends && trends.length > 0 && (
          <div className="mb-3 max-h-60 overflow-y-auto rounded-lg border p-3">
            <div className="space-y-1">
              {trends.map((t, i) => (
                <button
                  key={i}
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm hover:bg-muted"
                  onClick={() => { setMaterial(t.title); setShowTrends(false); }}
                >
                  <span className="inline-block w-6 text-center text-xs font-bold text-muted-foreground">{i + 1}</span>
                  <span className="flex-1">{t.title}</span>
                  <span className="text-xs text-muted-foreground">{SOURCE_LABELS[t.source] || t.source}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        <Textarea
          value={material}
          onChange={(e) => setMaterial(e.target.value)}
          placeholder="输入你的素材，或点击上方选择热点话题..."
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
