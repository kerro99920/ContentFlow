import Link from "next/link";
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="flex flex-col items-center justify-center gap-6 py-24 text-center">
      <h1 className="text-5xl font-bold tracking-tight">
        一个素材进，全平台内容出
      </h1>
      <p className="max-w-2xl text-xl text-muted-foreground">
        输入一段文字，AI 自动生成适配小红书、抖音、公众号、博客的专业内容。
        告别重复劳动，专注创作本身。
      </p>
      <div className="flex gap-4">
        <Link href="/register">
          <Button size="lg">免费开始</Button>
        </Link>
        <Link href="#features">
          <Button size="lg" variant="outline">了解更多</Button>
        </Link>
      </div>
    </section>
  );
}
