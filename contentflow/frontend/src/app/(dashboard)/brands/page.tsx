"use client";
import { useState } from "react";
import { BrandForm } from "@/components/brand/brand-form";
import { BrandList } from "@/components/brand/brand-list";

export default function BrandsPage() {
  const [refresh, setRefresh] = useState(0);
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">品牌模板</h1>
      <BrandForm onCreated={() => setRefresh((r) => r + 1)} />
      <div className="mt-8"><BrandList key={refresh} /></div>
    </div>
  );
}
