"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/auth";
import { UsageBadge } from "./usage-badge";

const navItems = [
  { href: "/generate", label: "内容生成" },
  { href: "/history", label: "历史记录" },
  { href: "/brands", label: "品牌模板" },
  { href: "/schedules", label: "自动任务" },
  { href: "/calendar", label: "日历" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* 移动端头部 */}
      <div className="flex items-center justify-between border-b p-3 md:hidden">
        <h2 className="text-lg font-bold">ContentFlow</h2>
        <Button variant="ghost" size="sm" onClick={() => setOpen(!open)}>
          {open ? "✕" : "☰"}
        </Button>
      </div>
      {/* 移动端下拉导航 */}
      {open && (
        <nav className="flex flex-col gap-1 border-b p-3 md:hidden">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} onClick={() => setOpen(false)}>
              <Button variant={pathname === item.href ? "secondary" : "ghost"} className="w-full justify-start" size="sm">
                {item.label}
              </Button>
            </Link>
          ))}
        </nav>
      )}
      {/* 桌面端侧边栏 */}
      <aside className="hidden h-screen w-56 flex-col border-r p-4 md:flex">
        <h2 className="mb-6 text-lg font-bold">ContentFlow</h2>
        <nav className="flex flex-1 flex-col gap-1">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href}>
              <Button variant={pathname === item.href ? "secondary" : "ghost"} className="w-full justify-start">
                {item.label}
              </Button>
            </Link>
          ))}
        </nav>
        <UsageBadge />
        <Button variant="outline" onClick={logout}>退出登录</Button>
      </aside>
    </>
  );
}
