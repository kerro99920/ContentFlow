"use client";
import { useState } from "react";
import { GenerateForm } from "@/components/content/generate-form";
import { PlatformTabs } from "@/components/content/platform-tabs";
import type { ContentItem } from "@/lib/types";

export default function GeneratePage() {
  const [results, setResults] = useState<ContentItem[]>([]);
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">生成内容</h1>
      <GenerateForm onGenerated={setResults} />
      {results.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">生成结果</h2>
          <PlatformTabs contents={results} />
        </div>
      )}
    </div>
  );
}
