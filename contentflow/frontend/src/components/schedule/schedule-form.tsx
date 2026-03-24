"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { PLATFORMS } from "@/lib/types";
import type { ScheduledTask } from "@/lib/types";

const CRON_PRESETS = [
  { label: "每天 9:00", value: "0 9 * * *" },
  { label: "每天 21:00", value: "0 21 * * *" },
  { label: "工作日 9:00", value: "0 9 * * 1-5" },
  { label: "每周一 9:00", value: "0 9 * * 1" },
];

const BRAND_TONES = [
  { value: "professional", label: "专业严谨" },
  { value: "casual", label: "轻松活泼" },
  { value: "seeding", label: "种草安利" },
];

interface Props {
  onCreated: () => void;
}

export function ScheduleForm({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [sourceMaterial, setSourceMaterial] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [brandTone, setBrandTone] = useState("casual");
  const [cronExpression, setCronExpression] = useState("0 9 * * *");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const togglePlatform = (value: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value]
    );
  };

  const handleSubmit = async () => {
    if (!name.trim() || !sourceMaterial.trim() || selectedPlatforms.length === 0) return;
    setLoading(true);
    setError("");
    try {
      await api.fetch<ScheduledTask>("/api/schedules", {
        method: "POST",
        body: JSON.stringify({
          name,
          source_material: sourceMaterial,
          platforms: selectedPlatforms,
          brand_tone: brandTone,
          cron_expression: cronExpression,
        }),
      });
      setName("");
      setSourceMaterial("");
      setSelectedPlatforms([]);
      setBrandTone("casual");
      setCronExpression("0 9 * * *");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader><CardTitle>新建自动任务</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>任务名称</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="例：每日产品推广" />
        </div>
        <div>
          <Label>素材内容</Label>
          <Textarea
            value={sourceMaterial}
            onChange={(e) => setSourceMaterial(e.target.value)}
            placeholder="输入要定期生成内容的素材..."
            rows={4}
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
          <Label>品牌调性</Label>
          <Select value={brandTone} onValueChange={(v) => { if (v !== null) setBrandTone(v); }}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {BRAND_TONES.map((t) => (
                <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>执行频率</Label>
          <Select value={cronExpression} onValueChange={(v) => { if (v !== null) setCronExpression(v); }}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {CRON_PRESETS.map((p) => (
                <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {error && <p className="text-sm text-red-500">{error}</p>}
        <Button
          onClick={handleSubmit}
          disabled={loading || !name.trim() || !sourceMaterial.trim() || selectedPlatforms.length === 0}
        >
          {loading ? "创建中..." : "创建任务"}
        </Button>
      </CardContent>
    </Card>
  );
}
