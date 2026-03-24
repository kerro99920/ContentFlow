"use client";
import { useState } from "react";
import { ScheduleForm } from "@/components/schedule/schedule-form";
import { ScheduleList } from "@/components/schedule/schedule-list";

export default function SchedulesPage() {
  const [refresh, setRefresh] = useState(0);
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">自动任务</h1>
      <ScheduleForm onCreated={() => setRefresh((r) => r + 1)} />
      <div className="mt-8"><ScheduleList key={refresh} /></div>
    </div>
  );
}
