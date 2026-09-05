"""
LLM 调用层 — 通义千问 API 封装

实际实现。app/llm.py 是薄委托层。
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

import httpx

from backend.app.config import settings

logger = logging.getLogger(__name__)


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
