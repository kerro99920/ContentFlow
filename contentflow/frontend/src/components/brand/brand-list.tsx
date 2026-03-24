"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { BrandProfile } from "@/lib/types";
import { toast } from "sonner";
import Link from "next/link";

export function BrandList() {
  const [profiles, setProfiles] = useState<BrandProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    api.fetch<BrandProfile[]>("/api/brand-profiles")
      .then((data) => setProfiles(data))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await api.fetch(`/api/brand-profiles/${id}`, { method: "DELETE" });
      setProfiles((prev) => prev.filter((p) => p.id !== id));
      toast.success("品牌模板已删除");
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <p className="text-sm text-muted-foreground">加载中...</p>;
  if (profiles.length === 0) return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      <div className="text-4xl">🏷️</div>
      <p className="text-muted-foreground">暂无品牌模板</p>
      <Link href="/brands"><Button>创建品牌模板</Button></Link>
    </div>
  );

  return (
    <div className="space-y-4">
      {profiles.map((profile) => (
        <Card key={profile.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{profile.name}</CardTitle>
              <Button
                variant="outline"
                size="sm"
                disabled={deletingId === profile.id}
                onClick={() => handleDelete(profile.id)}
              >
                {deletingId === profile.id ? "删除中..." : "删除"}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">{profile.tone_description}</p>
            {profile.industry_keywords && profile.industry_keywords.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {profile.industry_keywords.map((kw) => (
                  <Badge key={kw} variant="outline">{kw}</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
