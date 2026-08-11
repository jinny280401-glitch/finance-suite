"""
视频字幕/内容提取模块
支持 YouTube（通过Supadata API）、B站（直接API）、今日头条（SSR + VOD API）

独立CLI脚本，无内部依赖
用法: python3 video_data.py --url "https://youtube.com/watch?v=xxx"
"""

import re
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=3)

SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY", "")


def _extract_youtube_id(url: str) -> str | None:
    """从URL提取YouTube视频ID"""
    patterns = [
        r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _extract_bilibili_id(url: str) -> str | None:
    """从URL提取B站BV号"""
    m = re.search(r'(BV[a-zA-Z0-9]+)', url)
    return m.group(1) if m else None


def _fetch_youtube_transcript(video_id: str) -> dict:
    """通过Supadata REST API获取YouTube字幕"""
    if not SUPADATA_API_KEY:
        return {"success": False, "error": "Supadata API Key未配置（设置环境变量 SUPADATA_API_KEY）", "content": ""}

    import httpx

    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {"x-api-key": SUPADATA_API_KEY}

    # 尝试多种语言
    for lang in ["zh-Hans", "zh", "en", None]:
        try:
            params = {"url": url, "text": "true"}
            if lang:
                params["lang"] = lang
            resp = httpx.get(
                "https://api.supadata.ai/v1/youtube/transcript",
                params=params, headers=headers, timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", "")
                if content and len(content) > 50:
                    return {
                        "success": True,
                        "content": content,
                        "lang": data.get("lang", lang or "auto"),
                        "source": "supadata",
                    }
        except Exception:
            continue

    return {"success": False, "error": "该视频无可用字幕", "content": ""}


def _fetch_youtube_transcript_fallback(video_id: str) -> dict:
    """备用方案：通过免费第三方API获取字幕"""
    import httpx

    # 方案1: noembed获取视频标题和描述
    try:
        resp = httpx.get(
            f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}",
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", "")
            author = data.get("author_name", "")
            if title:
                return {
                    "success": True,
                    "content": f"视频标题：{title}\n作者：{author}\n(注：仅获取到标题信息，未获取到完整字幕)",
                    "lang": "metadata",
                    "source": "noembed",
                    "partial": True,
                    "title": title,
                    "author": author,
                }
    except Exception:
        pass

    return {"success": False, "error": "所有方案均失败", "content": ""}


def _fetch_bilibili_transcript(bvid: str) -> dict:
    """获取B站视频字幕"""
    import httpx

    try:
        # 获取CID
        resp = httpx.get(
            f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}",
            timeout=10
        )
        if resp.status_code != 200:
            return {"success": False, "error": "B站API请求失败", "content": ""}

        data = resp.json()
        if not data.get("data"):
            return {"success": False, "error": "未找到视频", "content": ""}

        cid = data["data"][0]["cid"]
        title = data["data"][0].get("part", "")

        # 获取视频信息
        info_resp = httpx.get(
            f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
            timeout=10
        )
        video_info = ""
        if info_resp.status_code == 200:
            info_data = info_resp.json().get("data", {})
            video_info = (
                f"标题：{info_data.get('title', '')}\n"
                f"UP主：{info_data.get('owner', {}).get('name', '')}\n"
                f"播放量：{info_data.get('stat', {}).get('view', '')}\n"
                f"简介：{info_data.get('desc', '')}\n"
            )

        # 尝试获取字幕
        sub_resp = httpx.get(
            f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}",
            timeout=10
        )
        if sub_resp.status_code == 200:
            sub_data = sub_resp.json()
            subtitles = sub_data.get("data", {}).get("subtitle", {}).get("subtitles", [])
            if subtitles:
                # 下载字幕内容
                sub_url = "https:" + subtitles[0]["subtitle_url"]
                sub_content_resp = httpx.get(sub_url, timeout=10)
                if sub_content_resp.status_code == 200:
                    sub_json = sub_content_resp.json()
                    texts = [item["content"] for item in sub_json.get("body", [])]
                    full_text = "\n".join(texts)
                    return {
                        "success": True,
                        "content": f"{video_info}\n字幕内容：\n{full_text}",
                        "lang": subtitles[0].get("lan", "zh"),
                        "source": "bilibili_subtitle",
                    }

        # 没有字幕，返回视频信息
        if video_info:
            return {
                "success": True,
                "content": video_info + "\n(该视频无CC字幕，以上为视频公开信息)",
                "lang": "metadata",
                "source": "bilibili_info",
                "partial": True,
            }

        return {"success": False, "error": "未获取到B站视频信息", "content": ""}
    except Exception as e:
        return {"success": False, "error": str(e), "content": ""}


# ============================================================
# 今日头条视频提取
# ============================================================


def _extract_toutiao_id(url: str) -> str | None:
    """从URL提取今日头条视频ID（group_id）。
    支持格式：
    - m.toutiao.com/video/{id}
    - www.toutiao.com/video/{id}
    - toutiao.com/video/{id}
    - toutiao.com/group/{id}
    """
    patterns = [
        r'toutiao\.com/video/(\d+)',
        r'toutiao\.com/group/(\d+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _fetch_toutiao_ssr(video_id: str) -> dict:
    """从今日头条 mobile SSR 页面提取视频元数据。
    直接解析 HTML 中 URL-encoded 的 SSR JSON payload，
    不需要浏览器渲染。

    返回 dict 包含 title, creator, duration, play_auth_token_v2 等。
    如果 SSR schema 变化导致解析失败，返回 provider_schema_changed 错误。
    """
    import json as _json
    from urllib.parse import unquote

    mobile_url = f"https://m.toutiao.com/video/{video_id}/"

    try:
        import httpx

        resp = httpx.get(
            mobile_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/16.0 Mobile/15E148 Safari/604.1"
                )
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"toutiao_ssr: HTTP {resp.status_code}",
                "content": "",
            }

        html = resp.text

        # 查找 URL-encoded SSR JSON（>20KB 的 inline script，以 %7B 开头）
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
        ssr_raw = None
        for s in scripts:
            s = s.strip()
            if len(s) > 20000 and s.startswith("%7B"):
                ssr_raw = s
                break

        if not ssr_raw:
            return {
                "success": False,
                "error": "provider_schema_changed: SSR payload not found in HTML",
                "content": "",
            }

        try:
            ssr_data = _json.loads(unquote(ssr_raw))
        except Exception as e:
            return {
                "success": False,
                "error": f"provider_schema_changed: SSR JSON parse failed — {e}",
                "content": "",
            }

        article = ssr_data.get("articleInfo")
        if not article or not isinstance(article, dict):
            return {
                "success": False,
                "error": "provider_schema_changed: articleInfo missing from SSR data",
                "content": "",
            }

        title = article.get("title", "")
        play_auth_token = article.get("playAuthTokenV2", "")
        video_duration = article.get("videoDuration", 0)
        media_user = article.get("mediaUser", {}) or {}
        creator = media_user.get("screenName", "") or article.get("source", "")

        return {
            "success": True,
            "title": title,
            "creator": creator,
            "duration_seconds": video_duration,
            "duration_formatted": (
                f"{video_duration // 60}m{video_duration % 60}s"
                if video_duration
                else ""
            ),
            "publish_time": article.get("publishTime", ""),
            "view_count": article.get("videoPlayCount", 0),
            "thumbnail": article.get("posterUrl", ""),
            "video_id": article.get("videoId", ""),
            "group_id": article.get("gid", video_id),
            "play_auth_token_v2": play_auth_token,
            "media_id": article.get("mediaId", ""),
            "source": "toutiao_ssr",
            "partial": True,
            "content": "",
            "ssr_article": article,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"toutiao_ssr exception: {e}",
            "content": "",
        }


def _fetch_toutiao_vod(play_auth_token: str, video_id: str) -> dict:
    """通过 ByteDance VOD GetPlayInfo API 获取视频 MP4 播放地址。

    play_auth_token 来自 SSR JSON 的 playAuthTokenV2 字段。
    返回的 MP4 URL 是临时签名 URL（约 24h 过期），不可长期缓存。
    """
    import json as _json
    import base64

    if not play_auth_token:
        return {
            "success": False,
            "error": "missing playAuthTokenV2 — VOD API not callable",
            "mp4_urls": [],
        }

    try:
        import httpx

        # 解码 base64 token → 提取 GetPlayInfoToken（签名过的 AWS 查询参数）
        padded = (
            play_auth_token + "=" * (4 - len(play_auth_token) % 4)
            if len(play_auth_token) % 4
            else play_auth_token
        )
        decoded = base64.b64decode(padded).decode("utf-8", errors="replace")
        token_data = _json.loads(decoded)
        api_params = token_data.get("GetPlayInfoToken", "")

        if not api_params:
            return {
                "success": False,
                "error": "missing GetPlayInfoToken in playAuthTokenV2 payload",
                "mp4_urls": [],
            }

        resp = httpx.get(
            f"https://vod.bytedanceapi.com/?{api_params}",
            timeout=15,
        )
        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"VOD API HTTP {resp.status_code}",
                "mp4_urls": [],
            }

        vod_data = resp.json()
        play_list = (
            vod_data.get("Result", {}).get("Data", {}).get("PlayInfoList", [])
        )

        mp4_urls = []
        for p in play_list:
            mp4_urls.append(
                {
                    "definition": p.get("Definition", "unknown"),
                    "bitrate": p.get("Bitrate", 0),
                    "width": p.get("Width", 0),
                    "height": p.get("Height", 0),
                    "size_bytes": p.get("Size", 0),
                    "main_url": p.get("MainPlayUrl", ""),
                    "backup_url": p.get("BackupPlayUrl", ""),
                    "url_expire": p.get("UrlExpire", 0),
                }
            )

        if not mp4_urls:
            return {
                "success": False,
                "error": "VOD API returned empty PlayInfoList",
                "mp4_urls": [],
            }

        return {
            "success": True,
            "mp4_urls": mp4_urls,
            "error": "",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"toutiao_vod exception: {e}",
            "mp4_urls": [],
        }


def _fetch_toutiao_video_info(video_id: str) -> dict:
    """Toutiao 视频信息提取编排器：SSR → VOD → 合并结果。

    SSR 失败 → 返回 provider_schema_changed（不尝试 VOD）。
    SSR 成功但 VOD 失败 → metadata PARTIAL success，video_urls 为空，
    transcript_status = unavailable_without_asr。
    """
    # Phase 1: SSR metadata
    ssr_result = _fetch_toutiao_ssr(video_id)
    if not ssr_result.get("success"):
        return ssr_result  # provider_schema_changed or HTTP error

    # Phase 2: VOD MP4 URLs
    play_token = ssr_result.get("play_auth_token_v2", "")
    vod_result = _fetch_toutiao_vod(play_token, video_id)

    # Merge
    mp4_urls = vod_result.get("mp4_urls", []) if vod_result.get("success") else []
    vod_error = vod_result.get("error", "")

    source_parts = ["toutiao_ssr"]
    if mp4_urls:
        source_parts.append("toutiao_vod")

    video_info = {
        "success": True,
        "title": ssr_result.get("title", ""),
        "creator": ssr_result.get("creator", ""),
        "duration_seconds": ssr_result.get("duration_seconds", 0),
        "duration_formatted": ssr_result.get("duration_formatted", ""),
        "publish_time": ssr_result.get("publish_time", ""),
        "view_count": ssr_result.get("view_count", 0),
        "thumbnail": ssr_result.get("thumbnail", ""),
        "video_id": ssr_result.get("video_id", ""),
        "group_id": video_id,
        "media_id": ssr_result.get("media_id", ""),
        "source": "+".join(source_parts),
        "mp4_urls": mp4_urls,
        "transcript_status": "unavailable_without_asr",
        "partial": len(mp4_urls) == 0,
        "content": "",
    }
    if vod_error:
        video_info["vod_error"] = vod_error

    return video_info


# ============================================================
# 统一入口
# ============================================================


async def get_video_content(url: str) -> dict:
    """
    从视频URL获取文字内容。
    返回 {"success": bool, "content": str, "source": str, "title": str}

    支持平台：
    - YouTube: 字幕提取（Supadata API → noembed fallback）
    - B站: 字幕提取（官方 API）
    - 今日头条: 视频信息提取（SSR → VOD API），不含字幕（需 ASR）
    """
    loop = asyncio.get_event_loop()

    # 判断平台
    yt_id = _extract_youtube_id(url)
    bili_id = _extract_bilibili_id(url)
    toutiao_id = _extract_toutiao_id(url)

    if yt_id:
        # YouTube: Supadata → fallback(noembed)
        result = await loop.run_in_executor(
            _executor, _fetch_youtube_transcript, yt_id
        )
        if not result["success"] or not result.get("content"):
            result = await loop.run_in_executor(
                _executor, _fetch_youtube_transcript_fallback, yt_id
            )
        return result

    elif bili_id:
        # B站
        result = await loop.run_in_executor(
            _executor, _fetch_bilibili_transcript, bili_id
        )
        return result

    elif toutiao_id:
        # 今日头条: SSR metadata → VOD MP4 URLs
        result = await loop.run_in_executor(
            _executor, _fetch_toutiao_video_info, toutiao_id
        )
        return result

    else:
        # 其他URL: 不支持
        return {
            "success": False,
            "error": "unsupported_platform",
            "content": "",
        }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="提取视频字幕/内容（支持YouTube、B站、今日头条）"
    )
    parser.add_argument(
        "--url", type=str, required=True, help="视频URL（YouTube/B站/今日头条）"
    )
    args = parser.parse_args()

    print(f"正在提取视频内容：{args.url} ...", flush=True)

    result = asyncio.run(get_video_content(args.url))

    if result.get("success"):
        print(f"\n来源：{result.get('source', 'unknown')}")
        if result.get("lang"):
            print(f"语言：{result.get('lang')}")
        if result.get("title"):
            print(f"标题：{result.get('title')}")
        if result.get("creator"):
            print(f"作者：{result.get('creator')}")
        if result.get("duration_formatted"):
            print(f"时长：{result.get('duration_formatted')}")
        if result.get("transcript_status"):
            print(f"字幕状态：{result.get('transcript_status')}")
        if result.get("mp4_urls"):
            print(f"视频源：{len(result['mp4_urls'])} 个清晰度")
        print(f"{'=' * 60}")
        if result.get("content"):
            print(result.get("content"))
        elif result.get("partial"):
            print("[部分提取 — 无字幕/正文文本]")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n提取失败：{result.get('error', '未知错误')}")
