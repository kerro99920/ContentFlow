"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ContentCard } from "./content-card";
import { Button } from "@/components/ui/button";
import type { ContentItem, ContentListResponse } from "@/lib/types";
import Link from "next/link";

interface Props {
  platform?: string;
  status?: string;
  search?: string;
}

export function ContentList({ platform, status, search }: Props) {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchPage = async (p: number) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(p), page_size: "10" });
      if (platform) params.set("platform", platform);
      if (status) params.set("status", status);
      const data = await api.fetch<ContentListResponse>(`/api/content?${params.toString()}`);
      setItems(data.items);
      setTotal(data.total);
      setPage(p);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPage(1); }, [platform, status]);

  const filtered = search
    ? items.filter((item) => (item.title || "").toLowerCase().includes(search.toLowerCase()))
    : items;

  const totalPages = Math.ceil(total / 10);

  if (loading) return <p className="text-muted-foreground">加载中...</p>;
  if (filtered.length === 0) return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      <div className="text-4xl">📝</div>
      <p className="text-muted-foreground">暂无内容</p>
      <Link href="/generate"><Button>去生成第一篇内容</Button></Link>
    </div>
  );

  return (
    <div className="space-y-4">
      {filtered.map((item) => (
        <ContentCard key={item.id} content={item} />
      ))}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={page <= 1} onClick={() => fetchPage(page - 1)}>上一页</Button>
          <span className="flex items-center text-sm text-muted-foreground">{page} / {totalPages}</span>
          <Button variant="outline" disabled={page >= totalPages} onClick={() => fetchPage(page + 1)}>下一页</Button>
        </div>
      )}
    </div>
  );
}
