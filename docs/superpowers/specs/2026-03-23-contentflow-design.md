# ContentFlow - AI 内容自动化平台设计文档

## Context

创始人是全栈 + AI 方向的技术开发者，拥有域名、博客（待填充内容）、抖音/小红书/微信账号。目标是创建个人公司，通过 SaaS 产品变现。核心需求是结合 AI Agent 工作流 + 内容自动化，面向内容创作者和小企业主，解决「一个素材需要手动适配多个平台」的效率痛点。

## 产品定位

**一句话**：一个素材进，全平台内容出。

**目标用户**：
- 自媒体人（同时运营 3+ 平台，日常被多平台内容适配消耗大量时间）
- 小企业主/运营（需要持续输出内容但没有专职团队）
- 知识付费/电商卖家（需要批量生产种草、测评、教程类内容）

**核心价值**：
- 输入一个核心素材 → AI 自动生成适配抖音/小红书/公众号/博客的内容
- 自定义品牌调性和人设模板，保证内容风格一致
- 工作流引擎支持自动化串联：生成 → 审核 → 修改 → 定时发布

## 功能架构

### 第一层：AI 内容生成引擎

核心能力，负责将一个素材转化为多平台适配内容。

**输入类型**：
- 文字（主题/大纲/产品描述）
- URL（自动提取网页内容作为素材）
- 音频（自动转文字后生成）
- 图片（OCR + 视觉理解后生成）

**输出平台及格式**：

| 平台 | 输出内容 | 格式要求 |
|------|----------|----------|
| 小红书 | 标题 + 正文 + 话题标签 + 封面文案建议 | 标题 ≤20字，正文 ≤1000字，emoji 风格 |
| 抖音 | 短视频脚本（分镜+台词+BGM建议+字幕文件） | 15-60s 时长，竖版 9:16，前3秒钩子 |
| 公众号 | 长文（标题+正文+摘要） | 支持 Markdown 转微信排版 |
| 博客 | SEO 优化文章（标题+正文+meta description+关键词） | 800-2000字，含 H2/H3 结构 |

**品牌调性系统**：
- 预设人设模板（专业严谨 / 轻松活泼 / 种草安利 / 知识科普）
- 自定义模板：用户描述品牌调性，系统生成 system prompt
- 行业词库：自动注入行业术语和热门表达

### 第二层：工作流引擎

轻量级 DAG（有向无环图）执行引擎。

**节点类型**：
- **触发节点**：手动 / 定时 (cron) / Webhook
- **AI 节点**：内容生成 / 内容改写 / 翻译 / 摘要
- **逻辑节点**：条件分支 / 循环 / 延时
- **输出节点**：保存草稿 / 通知（邮件/微信） / API 推送

**预设工作流模板**：
1. 「一键多平台」：输入素材 → 并行生成 4 平台内容 → 人工审核 → 保存
2. 「每日灵感」：定时抓取行业热点 → 生成内容建议 → 推送微信通知
3. 「竞品监控」：监控指定账号/关键词 → 生成分析报告 → 邮件通知
4. 「批量生产」：导入 CSV 产品列表 → 批量生成种草文案 → 导出

**可视化编排**（Phase 3）：
- 拖拽式画布编辑器
- 节点参数配置面板
- 实时执行日志和调试

### 第三层：数据与分析

**内容管理**：
- 内容日历视图：按日期查看各平台内容排期
- 内容状态管理：草稿 → 待审核 → 已审核 → 已发布
- 历史内容库：按平台/标签/日期筛选和搜索

**效果追踪**（初期手动回填，后期考虑 API 对接）：
- 各平台内容表现数据（阅读/点赞/评论/转发）
- 内容类型 × 平台的表现热力图
- 最佳发布时间分析

## 技术架构

```
┌─────────────────────────────────────────────┐
│                 前端 (Next.js)               │
│  Landing Page / Dashboard / 工作流编辑器     │
│  Tech: Next.js 14 + Tailwind + shadcn/ui    │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────┴──────────────────────────┐
│              后端 (FastAPI)                   │
│  用户系统 / 内容生成 / 工作流引擎 / 支付     │
│  Tech: Python 3.12 + FastAPI + SQLAlchemy   │
└──┬───────────┬───────────┬──────────────────┘
   │           │           │
   ▼           ▼           ▼
PostgreSQL   Redis      AI APIs
(数据持久化) (缓存/队列) (Claude/OpenAI)
                          │
                     Celery Workers
                     (异步任务/定时任务)
```

### 技术选型

| 组件 | 技术 | 理由 |
|------|------|------|
| 前端框架 | Next.js 14 (App Router) | SSR + SSG，SEO 友好（landing page 需要） |
| UI 组件 | shadcn/ui + Tailwind | 快速开发，视觉一致 |
| 后端框架 | FastAPI | Python 生态，AI 库丰富，async 性能好 |
| ORM | SQLAlchemy 2.0 | 成熟稳定，async 支持 |
| 数据库 | PostgreSQL | JSONB 存储灵活的内容结构 |
| 缓存/消息 | Redis | 会话缓存 + Celery broker |
| 任务队列 | Celery + Redis | AI 生成是耗时操作，必须异步 |
| AI 模型 | Claude API (主) + OpenAI (备) | 多模型路由，成本优化 |
| 认证 | JWT + OAuth2 | 微信扫码登录 + 邮箱注册 |
| 支付 | 微信支付 + 支付宝 | 国内用户主流支付方式 |
| 部署 | Vercel (前端) + 云服务器 (后端) | 前端 CDN 加速，后端灵活部署 |

### 数据模型（核心）

```
User
├── id, email, phone, wechat_openid
├── plan (free/pro/enterprise)
├── brand_profiles[] → BrandProfile
└── subscription → Subscription

BrandProfile
├── id, name, tone_description
├── system_prompt (AI 生成)
└── industry_keywords[]

Content
├── id, user_id, source_material
├── platform (xiaohongshu/douyin/wechat/blog)
├── title, body, tags, metadata (JSONB)
├── status (draft/reviewing/approved/published)
├── brand_profile_id
└── workflow_run_id (nullable)

Workflow
├── id, user_id, name
├── trigger_type (manual/cron/webhook)
├── dag_definition (JSONB) → 节点和边的定义
└── is_active

WorkflowRun
├── id, workflow_id
├── status (running/completed/failed)
├── started_at, finished_at
└── step_logs (JSONB)
```

## 分阶段交付

### Phase 1：核心闭环（4-5 周）

**目标**：上线一个能跑通「素材 → 多平台内容」闭环的最小可用产品。

**功能范围**：
- 用户注册/登录（仅邮箱，微信登录推迟到 Phase 2）
- Landing page（产品介绍 + 注册入口）
- 素材输入（仅文字，URL 提取推迟）
- AI 内容生成：仅小红书（先打透一个平台）
- 基础品牌调性选择（3 个预设模板）
- 内容历史记录
- 免费额度限制（每月 10 次）
- 基础设施搭建（数据库、部署、CI/CD）

**交付物**：
- 可访问的线上产品
- 邮箱用户系统
- 1 个平台的高质量内容生成

**并行推进**：营业执照注册、ICP 备案、微信开放平台申请

### Phase 2：扩展 + 付费（3-4 周）

**功能范围**：
- 增加公众号 + 博客平台适配
- 自定义品牌调性模板
- 付费订阅系统（微信支付）
- 基础工作流（预设模板，非可视化）
- 内容状态管理（草稿→审核→发布）
- 内容日历视图

### Phase 3：完整产品（4-6 周）

**功能范围**：
- 可视化工作流编排（拖拽画布）
- 定时任务和自动触发
- 音频/图片素材输入
- 数据分析面板
- 批量生成（CSV 导入）
- 团队协作功能（企业版）

## 获客策略

### 自有渠道（零成本启动）

**抖音**（核心获客渠道）：
- 内容方向：「我用 AI 3 分钟生成一周的小红书内容」实操演示
- 视频类型：产品演示 + before/after 对比 + 效率提升数据
- 频率：每日或隔日更新
- 参考本项目的「抖音策略师」Agent 的方法论

**小红书**（精准获客）：
- 内容方向：「自媒体效率工具」「AI 运营神器」种草笔记
- 强调真实使用场景和效果截图
- 参考本项目的「小红书专家」Agent 的方法论

**博客**（SEO 长尾流量）：
- 关键词：「AI 内容生成工具」「多平台内容自动化」「自媒体效率工具」
- 写对比评测文章，自然引流到产品

**微信**（私域转化）：
- 建种子用户微信群
- 收集反馈，快速迭代
- 参考本项目的「私域运营」Agent 的方法论

### 增长策略

- 免费版自带获客：免费用户生成的内容带「Powered by ContentFlow」水印/标记
- 邀请返利：邀请新用户注册，双方各得额外生成次数
- KOL 合作：给自媒体博主免费账号换测评视频

## 变现模式

| 套餐 | 月价 | 年价 | 内容 |
|------|------|------|------|
| 免费版 | ¥0 | - | 每月 10 次生成，2 平台，预设模板 |
| 专业版 | ¥99 | ¥999 | 无限生成，4 平台，5 工作流，自定义模板 |
| 企业版 | ¥299 | ¥2999 | 团队协作，API 接入，无限工作流，优先支持 |

## 前置条件与依赖

### 法务/资质（需立即启动，耗时最长）

| 事项 | 预估时间 | 是否阻塞 |
|------|----------|----------|
| 个体工商户/公司注册 | 1-2 周 | 阻塞支付接入 |
| 域名 ICP 备案 | 2-4 周 | 阻塞微信登录、支付 |
| 微信开放平台应用审批 | 1-2 周（ICP 之后） | 阻塞微信扫码登录 |
| 微信支付商户号 | 1-2 周（营业执照之后） | 阻塞付费功能 |

**关键决策**：Phase 1 不依赖这些资质——使用邮箱注册 + 免费模式先上线。资质办理与开发并行推进，Phase 2 再接入微信登录和支付。

### 临时替代方案

- **登录**：Phase 1 仅邮箱注册，Phase 2 加微信扫码
- **支付**：如果商户号未批下来，Phase 2 可先用 Stripe（支持国际用户）或手动对接（微信转账 + 手动开通）
- **发布**：小红书/抖音没有公开的内容发布 API，所有阶段均为「生成 + 导出」模式，用户手动复制发布。公众号有 API，后期可对接自动发布。

## Phase 1 API 设计

### 认证

```
POST   /api/auth/register          # 邮箱注册
POST   /api/auth/login             # 邮箱登录
POST   /api/auth/refresh           # 刷新 token
```

### 内容生成

```
POST   /api/content/generate       # 提交生成任务（异步）
GET    /api/content/tasks/{id}     # 查询生成任务状态
GET    /api/content                # 内容列表（分页）
GET    /api/content/{id}           # 内容详情
PUT    /api/content/{id}           # 编辑内容
DELETE /api/content/{id}           # 删除内容
```

### 用户

```
GET    /api/user/me                # 当前用户信息 + 用量
GET    /api/user/usage             # 当月用量统计
```

### 错误响应格式

```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "本月免费额度已用完",
    "detail": null
  }
}
```

HTTP 状态码：400 参数错误 / 401 未认证 / 403 权限不足 / 404 不存在 / 429 频率限制 / 500 服务端错误。

## Prompt 工程策略

### Prompt 模板管理
- 每个平台一套 prompt 模板，存储在数据库中，支持版本管理
- 模板变量：`{source_material}`, `{brand_tone}`, `{industry_keywords}`, `{platform_rules}`
- 每次生成记录使用的 prompt 版本，便于追踪和回滚

### 输出质量校验
- **格式校验**：标题长度、正文长度、标签数量是否符合平台规范
- **内容校验**：检测是否包含绝对化用语（"最好""第一"）、敏感词
- **重试机制**：校验不通过时自动重试（最多 2 次），仍不通过则返回并标记需人工修改

### AI 模型路由
- 默认使用 Claude API（质量优先）
- 降级路径：Claude 不可用 → OpenAI GPT-4o → 返回错误
- 成本控制：免费用户使用较便宜的模型（Claude Haiku / GPT-4o-mini）

## 安全考虑

- **输入校验**：用户提交的 URL 进行白名单域名检查，防止 SSRF
- **Prompt 注入防护**：用户输入与系统 prompt 严格隔离，使用 Claude 的 user/assistant 分离
- **数据隐私**：用户内容加密存储，数据库启用 TLS，定期备份
- **API 安全**：JWT token 过期时间 2h，refresh token 7d，rate limiting（免费用户 10 req/min）
- **隐私政策**：上线前准备隐私政策页面，说明数据收集和使用方式

## 基础设施

| 组件 | 方案 | 理由 |
|------|------|------|
| 前端托管 | Vercel | 免费 tier 够用，CDN 加速 |
| 后端托管 | 阿里云 ECS / Railway | 灵活部署，成本可控 |
| PostgreSQL | Supabase 或阿里云 RDS | 托管服务，免运维 |
| Redis | Upstash 或阿里云 Redis | 托管，按量付费 |
| 异步任务 | FastAPI BackgroundTasks (Phase 1) → arq (Phase 2+) | Phase 1 简单够用，避免 Celery 的运维负担 |
| 日志 | 阿里云 SLS 或 Sentry | 错误追踪和日志聚合 |
| CI/CD | GitHub Actions | 自动测试 + 部署 |

## 补充数据模型

```
Subscription
├── id, user_id
├── plan (free/pro/enterprise)
├── status (active/cancelled/expired)
├── started_at, expires_at
├── payment_provider, payment_ref
└── auto_renew

UsageRecord
├── id, user_id
├── period (2026-03 格式)
├── generation_count
└── last_reset_at

PromptTemplate
├── id, platform, version
├── system_prompt, user_prompt_template
├── is_active
└── created_at

Referral
├── id, inviter_id, invitee_id
├── reward_status (pending/credited)
└── created_at
```

## 竞品对比与差异化

| 特性 | ContentFlow | Coze/扣子 | 通用 AI 写作工具 |
|------|-------------|-----------|------------------|
| 多平台内容适配 | 核心功能，深度适配格式规范 | 需自己搭 bot | 不支持 |
| 品牌调性一致 | 内置人设系统 | 需自己写 prompt | 不支持 |
| 工作流自动化 | 面向内容场景的预设模板 | 通用但复杂 | 不支持 |
| 上手难度 | 输入素材即可用 | 需要理解 bot 构建 | 简单但功能单一 |
| 目标人群 | 内容创作者 | 开发者/技术用户 | 通用 |

**核心差异**：不做通用 AI 工作流平台，专注「内容创作者的多平台效率」这一个痛点，做到极致简单和深度适配。

## 验证方式

### Phase 1 上线后验证指标

| 指标 | 目标 | 验证什么 |
|------|------|----------|
| 注册用户 | 100+ | 产品吸引力 |
| 活跃生成次数 | 500+/月 | 核心功能是否有用 |
| 次日留存 | >20% | 体验是否足够好 |
| NPS | >30 | 用户是否愿意推荐 |
| 免费→付费转化 | >5% | 变现模型是否可行 |
