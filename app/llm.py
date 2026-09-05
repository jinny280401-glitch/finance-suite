import httpx
import json
import asyncio
from typing import AsyncGenerator

from app.config import settings


async def generate_analysis(
    system_prompt: str,
    user_content: str,
    search_results: str = "",
) -> str:
    """
    Call Qwen API to generate analysis report (non-streaming).
    Returns the generated text or an error message.
    """
    full_user_content = user_content
    if search_results:
        full_user_content += f"\n\n---\n以下是搜索到的参考资料：\n\n{search_results}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_user_content},
    ]

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                settings.QWEN_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.QWEN_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.QWEN_MODEL,
                    "messages": messages,
                    "temperature": 0.5,
                    "max_tokens": 6000,
                    "top_p": 0.8,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    except httpx.HTTPStatusError as e:
        return f"分析服务暂时不可用（HTTP {e.response.status_code}），请稍后重试。"
    except httpx.TimeoutException:
        return "分析请求超时，请稍后重试。"
    except (KeyError, IndexError):
        return "分析结果解析失败，请稍后重试。"
    except Exception:
        return "分析服务出现未知错误，请稍后重试。"


async def generate_analysis_stream(
    system_prompt: str,
    user_content: str,
    search_results: str = "",
) -> AsyncGenerator[str, None]:
    """
    Call Qwen API with streaming. Yields text chunks as they arrive.
    """
    full_user_content = user_content
    if search_results:
        full_user_content += f"\n\n---\n以下是搜索到的参考资料：\n\n{search_results}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_user_content},
    ]

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream(
                "POST",
                settings.QWEN_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.QWEN_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.QWEN_MODEL,
                    "messages": messages,
                    "temperature": 0.5,
                    "max_tokens": 6000,
                    "top_p": 0.8,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"\n\n[分析生成出错: {str(e)}]"


# ---- 简易缓存 ----
_cache: dict = {}
_cache_ttl = 600  # 10分钟


def _cache_key(skill_type: str, query: str) -> str:
    return f"{skill_type}:{query.strip().lower()}"


def cache_get(skill_type: str, query: str) -> dict | None:
    import time
    key = _cache_key(skill_type, query)
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["time"] < _cache_ttl:
            return entry["data"]
        else:
            del _cache[key]
    return None


def cache_set(skill_type: str, query: str, data: dict):
    import time
    key = _cache_key(skill_type, query)
    _cache[key] = {"data": data, "time": time.time()}
    # 清理过期缓存（保留最多50条）
    if len(_cache) > 50:
        oldest = sorted(_cache.items(), key=lambda x: x[1]["time"])[:10]
        for k, _ in oldest:
            del _cache[k]
