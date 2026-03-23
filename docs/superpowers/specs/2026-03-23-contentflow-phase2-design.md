# ContentFlow Phase 2 设计文档

## Context

Phase 1 已完成并部署：邮箱认证、小红书内容生成（OminiLink → Gemini 2.5 Pro）、内容历史、用量配额。后端运行在宁波云服务器（114.66.57.133:8000），前端本地开发。现在需要扩展到多平台、工作流自动化、品牌模板、内容管理增强。

### 与 Phase 1 设计的变更说明

- **付费订阅**：推迟到 Phase 3（需营业执照，暂未办理）
- **内容状态流**：简化为 `draft → approved → published`（去掉 `reviewing`，个人用户不需要审核流）
- **异步任务**：Phase 1 用 BackgroundTasks 做生成任务，Phase 2 新增 APScheduler 做定时调度（两者并存，各管各的）
- **抖音平台**：Phase 1 原计划不含抖音，Phase 2 一并加入

## 模块 1：多平台内容生成

### 目标
在现有小红书基础上增加抖音、公众号、博客三个平台的内容生成能力，支持一次素材同时生成多个平台内容。

### 新增平台 Prompt 模板

**抖音脚本** (`prompts/douyin.py`)：
- 输出 JSON：`{script_sections: [{time, scene, dialogue, camera}], bgm_suggestion, subtitle_text, hook}`
- 3 种调性模板（专业/轻松/种草）
- 约束：15-60s 时长，前 3 秒必须有钩子，竖版 9:16

**公众号长文** (`prompts/wechat.py`)：
- 输出 JSON：`{title, body, summary, tags}`
- 3 种调性模板
- 约束：800-2000 字，Markdown 格式，含引导关注语

**博客 SEO 文章** (`prompts/blog.py`)：
- 输出 JSON：`{title, body, meta_description, keywords, headings}`
- 3 种调性模板
- 约束：800-2000 字，H2/H3 结构，meta description ≤160 字

### 输出校验器

每个平台一个校验函数，加入现有 `VALIDATORS` dict：

| 平台 | 校验规则 |
|------|----------|
| douyin | script_sections 非空，有 hook 字段 |
| wechat | 标题 ≤64 字，正文 800-2000 字 |
| blog | 有 meta_description，keywords 为 list |

### 批量生成 API

新增 `POST /api/content/generate-batch` 端点：
- 请求：`{source_material, platforms: ["xiaohongshu", "douyin", "wechat", "blog"], brand_tone}`
- 行为：为每个平台创建独立的 GenerationTask，并行生成
- 响应：`{task_ids: {xiaohongshu: "uuid", douyin: "uuid", ...}}`
- 用量计费：每个平台算 1 次配额
- 配额不足处理：请求前检查剩余配额，若不足以覆盖所有平台则整体拒绝（不做部分生成）
- 部分失败处理：单个平台生成失败不影响其他平台，前端按 task 状态分别展示成功/失败

### 前端变更

- 生成表单：平台选择改为多选 checkbox（可同时选多个平台）
- 生成结果：按 tab 展示各平台内容
- 各平台内容卡片适配不同格式（抖音显示分镜表格，公众号显示长文预览）

## 模块 2：工作流自动化

### 目标
用户可设定定时任务，自动生成内容并通过邮件通知。

### 数据模型

```
ScheduledTask
├── id: UUID
├── user_id: UUID (FK)
├── name: str (任务名称)
├── cron_expression: str ("0 9 * * *" = 每天 9 点)
├── source_material: str (素材/主题描述)
├── platforms: list[str] (["xiaohongshu", "douyin"])
├── brand_tone: str
├── brand_profile_id: UUID | None
├── is_active: bool
├── last_run_at: datetime | None
├── created_at: datetime
```

### API 端点

```
POST   /api/schedules          # 创建定时任务
GET    /api/schedules          # 列出我的定时任务
PUT    /api/schedules/{id}     # 更新定时任务
DELETE /api/schedules/{id}     # 删除定时任务
POST   /api/schedules/{id}/run # 手动触发一次
```

### 定时执行引擎

- 使用 APScheduler（AsyncIOScheduler）
- 应用启动时从数据库加载所有 active 任务
- 每次执行：调用批量生成 → 等待完成 → 发送邮件通知
- 执行日志记录到 ScheduledTaskRun 表
- ScheduledTask 表为唯一 source of truth，启动时加载到 APScheduler（不使用 APScheduler 自带 job store）
- 已知限制：服务重启时进行中的定时任务会丢失，MVP 阶段可接受

```
ScheduledTaskRun
├── id: UUID
├── scheduled_task_id: UUID (FK)
├── status: str (running/completed/failed)
├── started_at: datetime
├── finished_at: datetime | None
├── error_message: str | None
├── generated_content_ids: list[UUID] (JSON)
```

### 邮件通知

- 使用 Python `aiosmtplib` + 免费 SMTP（如 Gmail SMTP 或 QQ 邮箱 SMTP）
- 邮件内容：各平台生成结果预览 + 链接到 dashboard 查看完整内容
- 配置项：`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
- SMTP 未配置时：跳过邮件发送，仅在 dashboard 显示结果
- 发送失败时：记录错误到 ScheduledTaskRun，不影响内容生成结果

### 前端变更

- 新增「自动任务」页面（侧边栏加入导航）
- 任务创建表单：名称、素材、平台选择、调性、cron 表达式（提供预设选项：每天/每周一三五/自定义）
- 任务列表：显示状态、上次执行时间、开关切换
- 手动执行按钮

## 模块 3：自定义品牌调性模板

### 目标
用户可创建和管理自己的品牌人设模板，生成内容时选用。

### 数据模型

启用 Phase 1 设计的 BrandProfile 模型：

```
BrandProfile
├── id: UUID
├── user_id: UUID (FK)
├── name: str ("我的电商号")
├── tone_description: str (用户描述的调性)
├── system_prompt: str (AI 根据描述生成的 prompt)
├── industry_keywords: list[str]
├── created_at: datetime
```

### API 端点

```
POST   /api/brand-profiles           # 创建（AI 自动生成 system_prompt）
GET    /api/brand-profiles           # 列出我的模板
PUT    /api/brand-profiles/{id}      # 更新
DELETE /api/brand-profiles/{id}      # 删除
```

### 创建流程

1. 用户输入：模板名称 + 调性描述（如"活泼的美妆博主，经常用口语和 emoji"）+ 行业关键词
2. 后端调用 AI 生成 system_prompt（基于调性描述）
3. 保存到数据库
4. 生成内容时，若选了自定义模板，用该模板的 system_prompt 替代预设调性

### 前端变更

- 新增「品牌模板」页面
- 模板创建/编辑表单
- 生成表单：调性选择器增加「我的模板」分组（预设模板 + 自定义模板）

## 模块 4：内容管理增强

### 目标
支持内容编辑、状态流转、日历视图、一键复制。

### 内容编辑

- `PUT /api/content/{id}` 端点（Phase 1 设计中已有，未实现）
- 请求：`{title, body, tags, status}`
- 前端：内容卡片增加「编辑」按钮，弹出编辑模态框

### 状态管理

状态流转：`draft` → `approved` → `published`
- 每个状态有对应的 badge 颜色
- 用户手动切换状态（标记为「已发布」表示已手动发到平台）

### 日历视图

- `GET /api/content/calendar?month=2026-03` 端点
- 返回：按日期分组的内容列表
- 前端：月视图日历，每天格子里显示内容数量和平台图标，点击查看详情

### 一键复制

- 每个内容卡片增加「复制」按钮
- 点击后将标题 + 正文 + 标签格式化后复制到剪贴板
- 不同平台格式不同（小红书加 emoji 和 #标签，公众号 Markdown，博客带 meta）

## 平台调度机制

`generation_service.py` 重构为平台注册表模式：

```python
PLATFORM_PROMPTS = {
    "xiaohongshu": (xiaohongshu.build_system_prompt, xiaohongshu.build_user_prompt),
    "douyin": (douyin.build_system_prompt, douyin.build_user_prompt),
    "wechat": (wechat.build_system_prompt, wechat.build_user_prompt),
    "blog": (blog.build_system_prompt, blog.build_user_prompt),
}
```

生成时根据 `platform` 查表获取对应的 prompt builder。若有自定义 brand_profile，用其 `system_prompt` 替代预设模板。

## 数据库迁移

Phase 2 需要执行 Alembic 迁移：
- 新建表：`scheduled_tasks`, `scheduled_task_runs`, `brand_profiles`
- 修改表：`contents` 增加 `brand_profile_id` 列（nullable FK）

部署时执行：`alembic revision --autogenerate -m "phase2 tables"` → `alembic upgrade head`

## 内容编辑 Schema

```python
class ContentUpdateRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    status: str | None = None  # draft/approved/published
```

所有字段 optional，部分更新。

## 日历 API 过滤

`GET /api/content/calendar?month=2026-03&platform=xiaohongshu&status=published`

支持 platform 和 status 可选过滤参数。

## 技术变更汇总

### 后端新增文件

```
app/prompts/douyin.py          # 抖音 prompt 模板
app/prompts/wechat.py          # 公众号 prompt 模板
app/prompts/blog.py            # 博客 prompt 模板
app/models/schedule.py         # ScheduledTask, ScheduledTaskRun 模型
app/models/brand_profile.py    # 启用（Phase 1 已设计）
app/schemas/schedule.py        # 定时任务 schemas
app/schemas/brand_profile.py   # 品牌模板 schemas
app/routers/schedule.py        # 定时任务 API
app/routers/brand_profile.py   # 品牌模板 API
app/services/schedule_service.py   # APScheduler + 执行逻辑
app/services/email_service.py      # 邮件发送
app/services/brand_service.py      # 品牌模板 CRUD + AI 生成 prompt
```

### 后端修改文件

```
app/config.py                  # 新增 SMTP 配置
app/main.py                    # 注册新 router，启动 scheduler
app/routers/content.py         # 新增 generate-batch、PUT、calendar 端点
app/services/generation_service.py  # 支持自定义 brand_profile 的 prompt
app/prompts/xiaohongshu.py     # 重构：支持自定义 system_prompt 注入
```

### 前端新增文件

```
src/app/(dashboard)/schedules/page.tsx    # 自动任务页
src/app/(dashboard)/brands/page.tsx       # 品牌模板页
src/app/(dashboard)/calendar/page.tsx     # 日历视图页
src/components/content/platform-tabs.tsx  # 多平台 tab 展示
src/components/content/edit-modal.tsx     # 内容编辑弹窗
src/components/content/copy-button.tsx    # 一键复制按钮
src/components/schedule/schedule-form.tsx # 任务创建表单
src/components/schedule/schedule-list.tsx # 任务列表
src/components/brand/brand-form.tsx       # 模板创建表单
src/components/brand/brand-list.tsx       # 模板列表
src/components/calendar/month-view.tsx    # 月视图日历组件
```

### 前端修改文件

```
src/components/dashboard/sidebar.tsx      # 新增导航项
src/components/content/generate-form.tsx  # 多平台多选 + 品牌模板选择
src/components/content/content-card.tsx   # 增加编辑/复制/状态按钮
src/lib/types.ts                          # 新增类型定义
```

### 新增依赖

- 后端：`apscheduler>=4.0`，`aiosmtplib>=3.0`
- 前端：无新增（用现有 shadcn 组件）

## 验证方式

| 场景 | 预期 |
|------|------|
| 一次素材生成 4 个平台内容 | 4 个 tab 各显示对应格式的内容 |
| 创建每日 9 点定时任务 | 到时间自动生成 + 收到邮件 |
| 创建自定义品牌模板 | 生成内容时可选择，内容风格匹配 |
| 编辑已生成内容 | 修改保存后更新显示 |
| 日历视图查看 3 月内容 | 按日期展示内容分布 |
| 一键复制小红书内容 | 剪贴板包含 emoji + #标签格式 |
