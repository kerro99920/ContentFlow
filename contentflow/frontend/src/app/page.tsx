import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { CTA } from "@/components/landing/cta";

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-4">
      <Hero />
      <Features />
      <CTA />
    </main>
  );
}
