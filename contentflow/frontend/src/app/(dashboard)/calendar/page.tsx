"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MonthView } from "@/components/calendar/month-view";

function formatMonth(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(() => new Date());

  const prevMonth = () => {
    setCurrentDate((d) => {
      const nd = new Date(d);
      nd.setDate(1);
      nd.setMonth(nd.getMonth() - 1);
      return nd;
    });
  };

  const nextMonth = () => {
    setCurrentDate((d) => {
      const nd = new Date(d);
      nd.setDate(1);
      nd.setMonth(nd.getMonth() + 1);
      return nd;
    });
  };

  const month = formatMonth(currentDate);

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">内容日历</h1>
      <div className="mb-4 flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={prevMonth}>上一月</Button>
        <span className="text-lg font-semibold">{month}</span>
        <Button variant="outline" size="sm" onClick={nextMonth}>下一月</Button>
      </div>
      <MonthView month={month} />
    </div>
  );
}
