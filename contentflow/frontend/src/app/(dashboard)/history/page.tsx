"use client";
import { useState } from "react";
import { ContentList } from "@/components/content/content-list";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";

export default function HistoryPage() {
  const [platform, setPlatform] = useState("all");
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">历史记录</h1>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input placeholder="搜索标题..." value={search} onChange={(e) => setSearch(e.target.value)} className="sm:w-48" />
        <Select value={platform} onValueChange={(v) => { if (v) setPlatform(v); }}>
          <SelectTrigger className="sm:w-32"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部平台</SelectItem>
            <SelectItem value="xiaohongshu">小红书</SelectItem>
            <SelectItem value="douyin">抖音</SelectItem>
            <SelectItem value="wechat">公众号</SelectItem>
            <SelectItem value="blog">博客</SelectItem>
            <SelectItem value="twitter">Twitter/X</SelectItem>
            <SelectItem value="bilibili">B站</SelectItem>
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={(v) => { if (v) setStatus(v); }}>
          <SelectTrigger className="sm:w-32"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="draft">草稿</SelectItem>
            <SelectItem value="approved">已审核</SelectItem>
            <SelectItem value="published">已发布</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <ContentList platform={platform === "all" ? undefined : platform} status={status === "all" ? undefined : status} search={search} />
    </div>
  );
}
