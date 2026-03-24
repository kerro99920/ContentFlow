"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ScheduledTask } from "@/lib/types";
import { toast } from "sonner";
import Link from "next/link";

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: "小红书", douyin: "抖音", wechat: "公众号", blog: "博客",
};

export function ScheduleList() {
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);

  useEffect(() => {
    api.fetch<ScheduledTask[]>("/api/schedules")
      .then((data) => setTasks(data))
      .finally(() => setLoading(false));
  }, []);

  const toggleActive = async (task: ScheduledTask) => {
    setActionId(task.id);
    try {
      const updated = await api.fetch<ScheduledTask>(`/api/schedules/${task.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !task.is_active }),
      });
      setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } finally {
      setActionId(null);
    }
  };

  const runNow = async (id: string) => {
    setActionId(id);
    try {
      await api.fetch(`/api/schedules/${id}/run`, { method: "POST" });
      toast.success("任务已触发");
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (id: string) => {
    setActionId(id);
    try {
      await api.fetch(`/api/schedules/${id}`, { method: "DELETE" });
      setTasks((prev) => prev.filter((t) => t.id !== id));
      toast.success("任务已删除");
    } finally {
      setActionId(null);
    }
  };

  if (loading) return <p className="text-sm text-muted-foreground">加载中...</p>;
  if (tasks.length === 0) return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      <div className="text-4xl">⏰</div>
      <p className="text-muted-foreground">暂无自动任务</p>
      <Link href="/schedules"><Button>创建自动任务</Button></Link>
    </div>
  );

  return (
    <div className="space-y-4">
      {tasks.map((task) => (
        <Card key={task.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{task.name}</CardTitle>
              <Badge variant={task.is_active ? "default" : "secondary"}>
                {task.is_active ? "运行中" : "已暂停"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-1">
              {task.platforms.map((p) => (
                <Badge key={p} variant="outline">{PLATFORM_LABELS[p] ?? p}</Badge>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">Cron: {task.cron_expression}</p>
            {task.last_run_at && (
              <p className="text-sm text-muted-foreground">
                上次执行：{new Date(task.last_run_at).toLocaleString("zh-CN")}
              </p>
            )}
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={actionId === task.id}
                onClick={() => toggleActive(task)}
              >
                {task.is_active ? "暂停" : "启用"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={actionId === task.id}
                onClick={() => runNow(task.id)}
              >
                立即执行
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={actionId === task.id}
                onClick={() => handleDelete(task.id)}
              >
                删除
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
