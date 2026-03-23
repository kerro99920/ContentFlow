"use client";
import { useState } from "react";
import { GenerateForm } from "@/components/content/generate-form";
import { ContentCard } from "@/components/content/content-card";
import type { ContentItem } from "@/lib/types";

export default function GeneratePage() {
  const [result, setResult] = useState<ContentItem | null>(null);

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">生成小红书内容</h1>
      <GenerateForm onGenerated={setResult} />
      {result && (
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">生成结果</h2>
          <ContentCard content={result} />
        </div>
      )}
    </div>
  );
}
