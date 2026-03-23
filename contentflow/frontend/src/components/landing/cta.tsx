import Link from "next/link";
import { Button } from "@/components/ui/button";

export function CTA() {
  return (
    <section className="py-20 text-center">
      <h2 className="mb-4 text-3xl font-bold">每月 10 次免费生成</h2>
      <p className="mb-8 text-muted-foreground">无需信用卡，立即体验 AI 内容生成</p>
      <Link href="/register">
        <Button size="lg">免费注册</Button>
      </Link>
    </section>
  );
}
