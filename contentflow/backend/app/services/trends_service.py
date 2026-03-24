"""获取各平台热点话题"""
import httpx


async def get_trending_topics() -> list[dict]:
    """从公开 API 获取热搜，返回 [{title, source, hot_score, url}]"""
    topics = []
    topics.extend(await _fetch_weibo())
    topics.extend(await _fetch_baidu())
    topics.extend(await _fetch_douyin())
    return topics[:30]


async def _fetch_weibo() -> list[dict]:
    """微博热搜"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://weibo.com/ajax/side/hotSearch")
            data = resp.json().get("data", {}).get("realtime", [])
            return [
                {
                    "title": item.get("word", ""),
                    "source": "weibo",
                    "hot_score": item.get("num", 0),
                    "url": f"https://s.weibo.com/weibo?q=%23{item.get('word', '')}%23",
                }
                for item in data[:10]
                if item.get("word")
            ]
    except Exception:
        return []


async def _fetch_baidu() -> list[dict]:
    """百度热搜"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://top.baidu.com/api/board?platform=wise&tab=realtime"
            )
            cards = resp.json().get("data", {}).get("cards", [])
            items = cards[0].get("content", []) if cards else []
            return [
                {
                    "title": item.get("word", ""),
                    "source": "baidu",
                    "hot_score": int(item.get("hotScore", 0)),
                    "url": item.get("url", ""),
                }
                for item in items[:10]
                if item.get("word")
            ]
    except Exception:
        return []


async def _fetch_douyin() -> list[dict]:
    """抖音热榜（通过公开接口）"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.douyin.com/aweme/v1/web/hot/search/list/",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            data = resp.json().get("data", {}).get("word_list", [])
            return [
                {
                    "title": item.get("word", ""),
                    "source": "douyin",
                    "hot_score": item.get("hot_value", 0),
                    "url": "",
                }
                for item in data[:10]
                if item.get("word")
            ]
    except Exception:
        return []
