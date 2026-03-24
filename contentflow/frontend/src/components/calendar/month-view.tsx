"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { ContentCard } from "@/components/content/content-card";
import { api } from "@/lib/api";
import type { CalendarResponse, CalendarDay } from "@/lib/types";

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: "红书", douyin: "抖音", wechat: "公众号", blog: "博客",
};

const WEEK_DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

interface Props {
  month: string; // YYYY-MM
}

function getDayOfWeek(dateStr: string): number {
  // Returns 0=Mon ... 6=Sun
  const d = new Date(dateStr + "T00:00:00");
  const day = d.getDay(); // 0=Sun, 1=Mon...6=Sat
  return day === 0 ? 6 : day - 1;
}

function getDaysInMonth(month: string): string[] {
  const [year, mon] = month.split("-").map(Number);
  const count = new Date(year, mon, 0).getDate();
  const days: string[] = [];
  for (let d = 1; d <= count; d++) {
    days.push(`${month}-${String(d).padStart(2, "0")}`);
  }
  return days;
}

export function MonthView({ month }: Props) {
  const [calData, setCalData] = useState<CalendarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedDay, setExpandedDay] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.fetch<CalendarResponse>(`/api/content/calendar?month=${month}`)
      .then((data) => setCalData(data))
      .finally(() => setLoading(false));
  }, [month]);

  if (loading) return <p className="text-sm text-muted-foreground">加载中...</p>;
  if (!calData) return <p className="text-sm text-red-500">加载失败</p>;

  const dayMap: Record<string, CalendarDay> = {};
  for (const day of calData.days) {
    dayMap[day.date] = day;
  }

  const allDays = getDaysInMonth(month);
  const firstDayOffset = getDayOfWeek(allDays[0]);

  // Build grid cells: leading empties + days
  const cells: (string | null)[] = [
    ...Array(firstDayOffset).fill(null),
    ...allDays,
  ];

  // Pad to complete rows
  while (cells.length % 7 !== 0) cells.push(null);

  const expandedDayData = expandedDay ? dayMap[expandedDay] : null;

  return (
    <div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-muted-foreground mb-1">
        {WEEK_DAYS.map((d) => <div key={d} className="py-1">{d}</div>)}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {cells.map((date, idx) => {
          if (!date) return <div key={`empty-${idx}`} className="h-20 rounded-md bg-muted/20" />;
          const day = dayMap[date];
          const count = day?.items.length ?? 0;
          const isExpanded = expandedDay === date;
          return (
            <div
              key={date}
              className={`h-20 rounded-md border p-1 cursor-pointer transition-colors hover:bg-muted/50 ${isExpanded ? "border-primary bg-muted/30" : "border-border"}`}
              onClick={() => setExpandedDay(isExpanded ? null : date)}
            >
              <div className="text-xs font-medium">{new Date(date + "T00:00:00").getDate()}</div>
              {count > 0 && (
                <div className="mt-1 space-y-0.5">
                  <div className="text-xs text-muted-foreground">{count} 条</div>
                  <div className="flex flex-wrap gap-0.5">
                    {[...new Set(day.items.map((i) => i.platform))].slice(0, 3).map((p) => (
                      <Badge key={p} variant="outline" className="px-0.5 text-[10px] h-3.5">
                        {PLATFORM_LABELS[p] ?? p}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
      {expandedDayData && expandedDayData.items.length > 0 && (
        <div className="mt-6 space-y-4">
          <h3 className="font-semibold text-sm">{expandedDay} 的内容</h3>
          {expandedDayData.items.map((item) => (
            <ContentCard key={item.id} content={item} />
          ))}
        </div>
      )}
    </div>
  );
}
