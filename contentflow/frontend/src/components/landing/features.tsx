const features = [
  {
    title: "多平台适配",
    description: "一次输入，自动生成适配小红书、抖音等平台规范的内容",
  },
  {
    title: "品牌调性一致",
    description: "预设多种风格模板，确保每篇内容都符合你的品牌人设",
  },
  {
    title: "AI 驱动",
    description: "基于顶级 AI 模型，生成高质量、高完播率的专业内容",
  },
];

export function Features() {
  return (
    <section id="features" className="py-20">
      <h2 className="mb-12 text-center text-3xl font-bold">核心能力</h2>
      <div className="grid gap-8 md:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className="rounded-lg border p-6">
            <h3 className="mb-2 text-xl font-semibold">{f.title}</h3>
            <p className="text-muted-foreground">{f.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
