"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/auth";
import { UsageBadge } from "./usage-badge";

const navItems = [
  { href: "/generate", label: "内容生成" },
  { href: "/history", label: "历史记录" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex h-screen w-56 flex-col border-r p-4">
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
  );
}
