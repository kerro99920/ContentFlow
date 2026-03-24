"""获取各平台热点话题（使用公开聚合 API）"""
import httpx


async def get_trending_topics() -> list[dict]:
    """从多个来源获取热搜，返回 [{title, source, hot_score, url}]"""
    topics = []
    for fetcher in [_fetch_toutiao, _fetch_baidu, _fetch_zhihu]:
        topics.extend(await fetcher())
    return topics[:30]


async def _fetch_toutiao() -> list[dict]:
    """今日头条热榜"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
            )
            data = resp.json().get("data", [])
            return [
                {
                    "title": item.get("Title", ""),
                    "source": "toutiao",
                    "hot_score": item.get("HotValue", 0),
                    "url": item.get("Url", ""),
                }
                for item in data[:10]
                if item.get("Title")
            ]
    except Exception:
        return []


async def _fetch_baidu() -> list[dict]:
    """百度热搜"""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
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


async def _fetch_zhihu() -> list[dict]:
    """知乎热榜"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            data = resp.json().get("data", [])
            return [
                {
                    "title": item.get("target", {}).get("title", ""),
                    "source": "zhihu",
                    "hot_score": item.get("detail_text", "0"),
                    "url": item.get("target", {}).get("url", ""),
                }
                for item in data[:10]
                if item.get("target", {}).get("title")
            ]
    except Exception:
        return []
