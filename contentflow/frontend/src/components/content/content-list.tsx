"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ContentCard } from "./content-card";
import { Button } from "@/components/ui/button";
import type { ContentItem, ContentListResponse } from "@/lib/types";

export function ContentList() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchPage = async (p: number) => {
    setLoading(true);
    try {
      const data = await api.fetch<ContentListResponse>(`/api/content?page=${p}&page_size=10`);
      setItems(data.items);
      setTotal(data.total);
      setPage(p);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPage(1); }, []);

  const totalPages = Math.ceil(total / 10);

  if (loading) return <p className="text-muted-foreground">加载中...</p>;
  if (items.length === 0) return <p className="text-muted-foreground">暂无内容，去生成第一篇吧</p>;

  return (
    <div className="space-y-4">
      {items.map((item) => (
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
