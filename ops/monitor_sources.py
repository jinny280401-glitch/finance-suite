#!/usr/bin/env python3
"""
Finance Suite market data source health monitor.

Cron example:
    */5 * * * * cd /Users/Zhuanz/finance-suite && /usr/bin/env python3 ops/monitor_sources.py --json >> logs/monitor_sources.cron.log 2>&1
"""

from __future__ import annotations

import argparse
import contextlib
import io
import importlib
import json
import logging
import multiprocessing
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
LOG_PATH = REPO_ROOT / "logs" / "monitor_sources.log"
SOURCE_PRIORITY = ["wind", "tushare", "joinquant", "akshare"]
DEFAULT_WIND_TIMEOUT = 5.0

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def configure_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def source_result(
    available: bool,
    start: float,
    error_type: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    return {
        "available": available,
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        "error_type": error_type,
        "message": message,
    }


def run_probe(name: str, probe: Callable[[], tuple[bool, str]]) -> dict[str, Any]:
    start = time.perf_counter()
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with suppress_process_output(), contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            available, message = probe()
        log_probe_noise(name, stdout_buffer.getvalue(), stderr_buffer.getvalue())
        return source_result(available, start, None if available else "unavailable", message)
    except ImportError as exc:
        log_probe_noise(name, stdout_buffer.getvalue(), stderr_buffer.getvalue())
        return source_result(False, start, "import_error", safe_message(exc))
    except TimeoutError as exc:
        log_probe_noise(name, stdout_buffer.getvalue(), stderr_buffer.getvalue())
        return source_result(False, start, "timeout", safe_message(exc))
    except Exception as exc:
        log_probe_noise(name, stdout_buffer.getvalue(), stderr_buffer.getvalue())
        return source_result(False, start, exc.__class__.__name__, safe_message(exc))


@contextlib.contextmanager
def suppress_process_output():
    """Suppress Python and native-extension stdout/stderr noise during probes."""
    sys.stdout.flush()
    sys.stderr.flush()
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            os.dup2(devnull.fileno(), 1)
            os.dup2(devnull.fileno(), 2)
            yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stdout_fd)
        os.close(stderr_fd)


def log_probe_noise(name: str, stdout_text: str, stderr_text: str) -> None:
    if stdout_text.strip():
        logging.info("%s probe stdout suppressed: %s", name, stdout_text.strip()[:500])
    if stderr_text.strip():
        logging.info("%s probe stderr suppressed: %s", name, stderr_text.strip()[:500])


def safe_message(exc: BaseException) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    return message[:300]


def wind_connection_worker(queue: multiprocessing.Queue) -> None:
    wind_data = importlib.import_module("wind_data")
    status = wind_data.check_connection()
    queue.put(status)


def probe_wind(timeout: float = DEFAULT_WIND_TIMEOUT) -> tuple[bool, str]:
    ctx = multiprocessing.get_context("fork")
    queue: multiprocessing.Queue = ctx.Queue()
    process = ctx.Process(target=wind_connection_worker, args=(queue,))
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join(1)
        raise TimeoutError("Wind probe timed out")

    if process.exitcode:
        return False, "Wind probe failed"

    status = queue.get_nowait() if not queue.empty() else {}
    available = bool(status.get("connected"))
    if available:
        return True, "Wind connection ok"
    return False, "Wind unavailable or not connected"


def probe_tushare() -> tuple[bool, str]:
    tushare_data = importlib.import_module("tushare_data")
    status = tushare_data.check_connection()
    available = bool(status.get("connected"))
    if available:
        return True, "Tushare Pro client initialized"
    return False, "Tushare Pro unavailable"


def probe_joinquant() -> tuple[bool, str]:
    joinquant_data = importlib.import_module("joinquant_data")
    check = getattr(joinquant_data, "check_joinquant_health", joinquant_data.check_connection)
    status = check()
    available = bool(status.get("connected"))
    if available and status.get("sample_query_ok") is False:
        return False, "JoinQuant auth ok but sample query failed"
    if available:
        return True, "JoinQuant connection ok"
    return False, str(status.get("error") or "JoinQuant unavailable or credentials missing")


def probe_akshare() -> tuple[bool, str]:
    module = importlib.import_module("akshare")
    version = getattr(module, "__version__", "unknown")
    return True, f"AkShare import ok version={version}"


def build_fallback(sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    active_source = next(
        (source for source in SOURCE_PRIORITY if sources[source]["available"]),
        None,
    )
    attempted_sources = SOURCE_PRIORITY if active_source is None else SOURCE_PRIORITY[: SOURCE_PRIORITY.index(active_source) + 1]
    return {
        "priority": SOURCE_PRIORITY,
        "active_source": active_source,
        "triggered": active_source != "wind",
        "attempted_sources": attempted_sources,
        "mcp_tool_fallback_ok": active_source is not None,
    }


def overall_status(sources: dict[str, dict[str, Any]], fallback: dict[str, Any]) -> str:
    if all(item["available"] for item in sources.values()):
        return "healthy"
    if fallback["mcp_tool_fallback_ok"]:
        return "degraded"
    return "failure"


def build_report(wind_timeout: float = DEFAULT_WIND_TIMEOUT) -> dict[str, Any]:
    probes: dict[str, Callable[[], tuple[bool, str]]] = {
        "wind": lambda: probe_wind(wind_timeout),
        "tushare": probe_tushare,
        "joinquant": probe_joinquant,
        "akshare": probe_akshare,
    }
    sources = {name: run_probe(name, probe) for name, probe in probes.items()}
    fallback = build_fallback(sources)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status(sources, fallback),
        "fallback": fallback,
        "sources": sources,
    }


def send_webhook(url: str, report: dict[str, Any], timeout: float) -> None:
    body = json.dumps(report, ensure_ascii=False, default=str).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status >= 400:
            raise RuntimeError(f"webhook returned HTTP {response.status}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor Finance Suite data sources.")
    parser.add_argument("--json", action="store_true", help="Print JSON health report.")
    parser.add_argument("--print-cron", action="store_true", help="Print a sample cron entry and exit.")
    parser.add_argument("--webhook-url", default="", help="POST health report to a webhook URL.")
    parser.add_argument("--webhook-timeout", type=float, default=5.0, help="Webhook timeout in seconds.")
    parser.add_argument("--wind-timeout", type=float, default=DEFAULT_WIND_TIMEOUT, help="Wind probe timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.print_cron:
        print("*/5 * * * * cd /Users/Zhuanz/finance-suite && /usr/bin/env python3 ops/monitor_sources.py --json >> logs/monitor_sources.cron.log 2>&1")
        return 0

    configure_logging()
    report = build_report(args.wind_timeout)
    logging.info("source health report: %s", json.dumps(report, ensure_ascii=False, default=str))

    if args.webhook_url:
        try:
            send_webhook(args.webhook_url, report, args.webhook_timeout)
            logging.info("webhook sent")
        except (OSError, urllib.error.URLError, RuntimeError) as exc:
            logging.warning("webhook failed: %s", safe_message(exc))

    output = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    print(output if args.json else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
