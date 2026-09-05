"""MCP tools: xueqiu_fetch, zhihu_fetch, sinafinance_fetch"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

# Tool 9: 雪球数据抓取（通过 autocli）
# ============================================================
@mcp.tool()
def xueqiu_fetch(command: str, symbol: str = "", limit: int = 10) -> str:
    """通过 autocli 抓取雪球数据（复用 Chrome 登录状态）。

    command 可选值：
    - hot: 雪球热门动态（大V观点、市场讨论）
    - hot-stock: 雪球热门股票榜（人气排行）
    - stock: 个股实时行情（需提供 symbol，如 SH600519）
    - watchlist: 自选股列表（需登录）
    - feed: 关注动态（需登录）
    - search: 搜索股票（需提供 symbol 作为关键词）
    - earnings-date: 财报发布日期（需提供 symbol）

    返回结构化 _qc 质检 JSON + JSON 格式数据。
    """
    try:
        import subprocess

        # 构建 autocli 命令
        autocli_path = os.path.expanduser("~/bin/autocli")
        if not os.path.exists(autocli_path):
            return _make_error_response("autocli 未安装，请先安装: curl -fsSL https://raw.githubusercontent.com/nashsu/AutoCLI/main/scripts/install.sh | sh")

        cmd = [autocli_path, "xueqiu", command]

        # 根据命令类型添加参数
        if command in ("stock", "earnings-date"):
            if not symbol:
                return _make_error_response(f"command={command} 需要提供 symbol 参数（如 SH600519）")
            cmd.append(symbol)
        elif command == "search":
            if not symbol:
                return _make_error_response("command=search 需要提供 symbol 参数作为搜索关键词")
            cmd.extend(["--query", symbol])

        # 添加通用参数
        if command not in ("stock", "earnings-date"):
            cmd.extend(["--limit", str(limit)])
        cmd.extend(["--format", "json"])

        # 设置环境变量（绕过代理）
        env = os.environ.copy()
        env["NO_PROXY"] = "localhost,127.0.0.1"
        env["no_proxy"] = "localhost,127.0.0.1"

        # 执行命令（某些命令如 hot-stock 可能需要更长时间）
        timeout_seconds = 60 if command in ("hot-stock", "feed") else 30
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "Not logged in" in error_msg or "HTTP 400" in error_msg:
                return _make_error_response(f"雪球未登录，请在 Chrome 中登录 xueqiu.com 后重试")
            elif "timeout" in error_msg.lower():
                return _make_error_response(f"autocli daemon 超时，请检查 Chrome 扩展是否已加载")
            else:
                return _make_error_response(f"autocli 执行失败: {error_msg}")

        # 解析 JSON 输出
        output = result.stdout.strip()
        if not output:
            return _make_error_response("autocli 返回空数据")

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return _make_error_response(f"autocli 返回非 JSON 数据: {output[:200]}")

        # 质检
        has_data = bool(data) and (isinstance(data, list) and len(data) > 0 or isinstance(data, dict))
        qc = {
            "status": "success" if has_data else "partial",
            "completeness": 1.0 if has_data else 0.5,
            "sources": ["xueqiu_autocli"],
            "fallback_source": None,
            "missing_dimensions": [] if has_data else ["数据为空"],
            "stale_data": [],
        }

        return _wrap_response(qc, json.dumps(data, ensure_ascii=False, indent=2))

    except subprocess.TimeoutExpired:
        return _make_error_response("autocli 执行超时（30秒），请检查网络或 Chrome 扩展状态")
    except Exception as e:
        return _make_error_response(f"xueqiu_fetch 异常: {e}")


# ============================================================


# Tool 10: 知乎数据抓取（通过 autocli）
# ============================================================
@mcp.tool()
def zhihu_fetch(command: str, query: str = "", question_id: str = "", limit: int = 10) -> str:
    """通过 autocli 抓取知乎数据（复用 Chrome 登录状态）。

    command 可选值：
    - hot: 知乎热榜（热度排名、问题标题、回答数）
    - search: 搜索知乎内容（需提供 query 关键词）
    - question: 问题详情和回答（需提供 question_id，从 URL 中获取）

    示例：
    - zhihu_fetch('hot', limit=10)
    - zhihu_fetch('search', query='人工智能')
    - zhihu_fetch('question', question_id='2031077519936287770', limit=5)

    返回结构化 _qc 质检 JSON + JSON 格式数据。
    """
    try:
        import subprocess

        autocli_path = os.path.expanduser("~/bin/autocli")
        if not os.path.exists(autocli_path):
            return _make_error_response("autocli 未安装")

        cmd = [autocli_path, "zhihu", command]

        if command == "search":
            if not query:
                return _make_error_response("command=search 需要提供 query 参数")
            cmd.append(query)
        elif command == "question":
            if not question_id:
                return _make_error_response("command=question 需要提供 question_id 参数")
            cmd.append(question_id)

        cmd.extend(["--limit", str(limit), "--format", "json"])

        env = os.environ.copy()
        env["NO_PROXY"] = "localhost,127.0.0.1"
        env["no_proxy"] = "localhost,127.0.0.1"

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "Not logged in" in error_msg or "HTTP 400" in error_msg:
                return _make_error_response("知乎未登录，请在 Chrome 中登录 zhihu.com 后重试")
            return _make_error_response(f"autocli 执行失败: {error_msg}")

        output = result.stdout.strip()
        if not output:
            return _make_error_response("autocli 返回空数据")

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return _make_error_response(f"autocli 返回非 JSON 数据: {output[:200]}")

        has_data = bool(data) and isinstance(data, list) and len(data) > 0
        qc = {
            "status": "success" if has_data else "partial",
            "completeness": 1.0 if has_data else 0.5,
            "sources": ["zhihu_autocli"],
            "fallback_source": None,
            "missing_dimensions": [] if has_data else ["数据为空（可能需要登录）"],
            "stale_data": [],
        }

        return _wrap_response(qc, json.dumps(data, ensure_ascii=False, indent=2))

    except subprocess.TimeoutExpired:
        return _make_error_response("autocli 执行超时（30秒）")
    except Exception as e:
        return _make_error_response(f"zhihu_fetch 异常: {e}")


def _autocli_run(platform: str, subcmd: list[str], timeout: int = 30) -> tuple[bool, any, str]:
    """通用 autocli 执行器，返回 (success, data, error_msg)"""
    import subprocess
    autocli_path = os.path.expanduser("~/bin/autocli")
    cmd = [autocli_path, platform] + subcmd + ["--format", "json"]
    env = os.environ.copy()
    env["NO_PROXY"] = "localhost,127.0.0.1"
    env["no_proxy"] = "localhost,127.0.0.1"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        if result.returncode != 0:
            return False, None, result.stderr.strip() or result.stdout.strip()
        data = json.loads(result.stdout.strip())
        return True, data, ""
    except subprocess.TimeoutExpired:
        return False, None, f"autocli 执行超时（{timeout}秒）"
    except json.JSONDecodeError as e:
        return False, None, f"JSON 解析失败: {e}"


# ============================================================


# Tool 11: 新浪财经实时快讯
# ============================================================
@mcp.tool()
def sinafinance_fetch(limit: int = 20) -> str:
    """抓取新浪财经 7x24 小时实时快讯。无需登录，直接调用 API。
    返回最新财经新闻，包含时间、内容、阅读量。
    返回结构化 _qc 质检 JSON。"""
    ok, data, err = _autocli_run("sinafinance", ["news", "--limit", str(limit)])
    if not ok:
        return _make_error_response(f"sinafinance_fetch 失败: {err}")
    has_data = bool(data)
    qc = {
        "status": "success" if has_data else "partial",
        "completeness": 1.0 if has_data else 0.0,
        "sources": ["sinafinance"],
        "fallback_source": None,
        "missing_dimensions": [] if has_data else ["数据为空"],
        "stale_data": [],
    }
    return _wrap_response(qc, json.dumps(data, ensure_ascii=False, indent=2))


# ============================================================


