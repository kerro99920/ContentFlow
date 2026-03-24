"use client";
import { useEffect, useState } from "react";
import { ContentCard } from "./content-card";
import { Button } from "@/components/ui/button";
import type { ContentItem } from "@/lib/types";

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: "小红书", douyin: "抖音", wechat: "公众号", blog: "博客", twitter: "Twitter/X", bilibili: "B站",
};

interface Props { contents: ContentItem[]; }

export function PlatformTabs({ contents }: Props) {
  const platforms = [...new Set(contents.map((c) => c.platform))];
  const [active, setActive] = useState(platforms[0] || "");

  useEffect(() => {
    const newPlatforms = [...new Set(contents.map((c) => c.platform))];
    if (newPlatforms.length > 0 && !newPlatforms.includes(active)) {
      setActive(newPlatforms[0]);
    } else if (newPlatforms.length > 0 && !active) {
      setActive(newPlatforms[0]);
    }
  }, [contents, active]);

  if (contents.length === 0) return null;

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {platforms.map((p) => (
          <Button key={p} variant={active === p ? "default" : "outline"} size="sm" onClick={() => setActive(p)}>
            {PLATFORM_LABELS[p] || p}
          </Button>
        ))}
      </div>
      {contents.filter((c) => c.platform === active).map((c) => (
        <ContentCard key={c.id} content={c} />
      ))}
    </div>
  );
}
