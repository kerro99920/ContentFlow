"""自动发布服务：通过浏览器自动化将内容发布到各平台"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext

# 会话存储目录
SESSION_DIR = Path(__file__).parent.parent.parent / "sessions"
SESSION_DIR.mkdir(exist_ok=True)


async def publish_to_platform(platform: str, content: dict, user_id: str) -> dict:
    """发布内容到指定平台，返回 {success, message, url}"""
    publishers = {
        "twitter": _publish_twitter,
        "xiaohongshu": _publish_xiaohongshu,
        "bilibili": _publish_bilibili,
    }
    publisher = publishers.get(platform)
    if not publisher:
        return {"success": False, "message": f"平台 {platform} 暂不支持自动发布"}

    try:
        return await publisher(content, user_id)
    except Exception as e:
        return {"success": False, "message": f"发布失败: {str(e)[:100]}"}


def _session_path(platform: str, user_id: str) -> str:
    return str(SESSION_DIR / f"{platform}_{user_id}.json")


async def _get_context(playwright, platform: str, user_id: str) -> BrowserContext:
    """获取带登录态的浏览器上下文"""
    session_file = _session_path(platform, user_id)
    browser = await playwright.chromium.launch(headless=True)
    if Path(session_file).exists():
        context = await browser.new_context(storage_state=session_file)
    else:
        context = await browser.new_context()
    return context


async def save_session(platform: str, user_id: str, context: BrowserContext):
    """保存登录态"""
    session_file = _session_path(platform, user_id)
    await context.storage_state(path=session_file)


async def login_to_platform(platform: str, user_id: str) -> dict:
    """启动有头浏览器让用户手动登录，登录完成后保存会话。
    返回 {success, message}"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        urls = {
            "twitter": "https://x.com/login",
            "xiaohongshu": "https://creator.xiaohongshu.com/login",
            "bilibili": "https://passport.bilibili.com/login",
        }
        url = urls.get(platform)
        if not url:
            await browser.close()
            return {"success": False, "message": f"不支持的平台: {platform}"}

        await page.goto(url)
        # 等待用户手动登录（最多 5 分钟）
        try:
            if platform == "twitter":
                await page.wait_for_url("**/home**", timeout=300000)
            elif platform == "xiaohongshu":
                await page.wait_for_url("**/publish**", timeout=300000)
            elif platform == "bilibili":
                await page.wait_for_url("**/member**", timeout=300000)

            await save_session(platform, user_id, context)
            await browser.close()
            return {"success": True, "message": f"{platform} 登录成功，会话已保存"}
        except Exception:
            await browser.close()
            return {"success": False, "message": "登录超时"}


async def _publish_twitter(content: dict, user_id: str) -> dict:
    """自动发推"""
    tweet_text = content.get("tweet") or content.get("body") or content.get("title", "")
    tags = content.get("tags", [])
    if tags:
        tweet_text += "\n\n" + " ".join(f"#{t}" for t in tags[:3])

    async with async_playwright() as p:
        context = await _get_context(p, "twitter", user_id)
        page = await context.new_page()

        try:
            await page.goto("https://x.com/compose/post", timeout=15000)
            await page.wait_for_timeout(2000)

            # 找到推文输入框
            editor = page.locator('[data-testid="tweetTextarea_0"]')
            await editor.click()
            await editor.fill(tweet_text)
            await page.wait_for_timeout(1000)

            # 点击发布按钮
            post_btn = page.locator('[data-testid="tweetButton"]')
            await post_btn.click()
            await page.wait_for_timeout(3000)

            await save_session("twitter", user_id, context)
            await context.close()
            return {"success": True, "message": "推文已发布", "url": "https://x.com"}
        except Exception as e:
            await context.close()
            return {"success": False, "message": f"Twitter 发布失败: {str(e)[:100]}"}


async def _publish_xiaohongshu(content: dict, user_id: str) -> dict:
    """自动发小红书笔记"""
    title = content.get("title", "")
    body = content.get("body", "")
    tags = content.get("tags", [])

    text = f"{body}\n\n" + " ".join(f"#{t}" for t in tags)

    async with async_playwright() as p:
        context = await _get_context(p, "xiaohongshu", user_id)
        page = await context.new_page()

        try:
            await page.goto("https://creator.xiaohongshu.com/publish/publish", timeout=15000)
            await page.wait_for_timeout(2000)

            # 点击"发布笔记"
            # 输入标题
            title_input = page.locator('input[placeholder*="标题"]').first
            if await title_input.is_visible():
                await title_input.fill(title)

            # 输入正文
            editor = page.locator('[contenteditable="true"]').first
            if await editor.is_visible():
                await editor.click()
                await editor.fill(text)

            await page.wait_for_timeout(1000)
            await save_session("xiaohongshu", user_id, context)
            await context.close()
            return {"success": True, "message": "小红书内容已填入创作者平台，请手动上传图片后发布"}
        except Exception as e:
            await context.close()
            return {"success": False, "message": f"小红书操作失败: {str(e)[:100]}"}


async def _publish_bilibili(content: dict, user_id: str) -> dict:
    """自动填入B站投稿信息"""
    title = content.get("title", "")
    description = content.get("description") or content.get("body", "")
    tags = content.get("tags", [])

    async with async_playwright() as p:
        context = await _get_context(p, "bilibili", user_id)
        page = await context.new_page()

        try:
            await page.goto("https://member.bilibili.com/platform/upload/text/edit", timeout=15000)
            await page.wait_for_timeout(2000)

            # 填入标题
            title_input = page.locator('input[placeholder*="标题"]').first
            if await title_input.is_visible():
                await title_input.fill(title)

            # 填入正文
            editor = page.locator('[contenteditable="true"]').first
            if await editor.is_visible():
                await editor.click()
                await editor.fill(description)

            await page.wait_for_timeout(1000)
            await save_session("bilibili", user_id, context)
            await context.close()
            return {"success": True, "message": "B站内容已填入，请检查后发布"}
        except Exception as e:
            await context.close()
            return {"success": False, "message": f"B站操作失败: {str(e)[:100]}"}


def get_supported_platforms() -> list[dict]:
    """返回支持自动发布的平台列表"""
    return [
        {"platform": "twitter", "name": "Twitter/X", "mode": "auto", "note": "全自动发布"},
        {"platform": "xiaohongshu", "name": "小红书", "mode": "semi", "note": "自动填入内容，需手动上传图片"},
        {"platform": "bilibili", "name": "B站", "mode": "semi", "note": "自动填入内容，需手动检查"},
    ]
