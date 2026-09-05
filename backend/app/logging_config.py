"""
集中日志配置

在应用启动最早期调用 setup_logging()，所有模块自动继承统一格式。

格式：
    2026-09-05 14:30:12.345 | INFO     | backend.engine.skills.stock_skill | fund_flow unavailable ...

特性：
    - 控制台：彩色输出（开发友好）
    - 文件：按大小轮转，保留 7 天（生产可追溯）
    - uvicorn 日志统一接管（不再用默认格式）
    - 第三方库（akshare/urllib3 等）降级到 WARNING
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── 格式定义 ──────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 第三方库降级，避免日志噪音
_NOISY_LOGGERS = {
    "urllib3": logging.WARNING,
    "urllib3.connectionpool": logging.WARNING,
    "akshare": logging.WARNING,
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "requests": logging.WARNING,
    "sqlalchemy.engine": logging.WARNING,
    "uvicorn.access": logging.INFO,
}


class _ColorFormatter(logging.Formatter):
    """控制台彩色 formatter（仅 TTY 生效）"""

    COLORS = {
        logging.DEBUG: "\033[36m",     # cyan
        logging.INFO: "\033[32m",      # green
        logging.WARNING: "\033[33m",   # yellow
        logging.ERROR: "\033[31m",     # red
        logging.CRITICAL: "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str | None = None,
    log_dir: str | Path | None = None,
) -> None:
    """
    初始化全局日志系统。

    Args:
        level: 日志级别，默认从环境变量 LOG_LEVEL 读取，缺省 INFO
        log_dir: 日志文件目录，None 则不写文件（开发模式）
    """
    level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, level, logging.INFO)

    root = logging.getLogger()

    # 避免重复初始化
    if root.handlers:
        return

    root.setLevel(numeric_level)

    # ── 控制台 handler ──
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(numeric_level)
    if sys.stderr.isatty():
        console.setFormatter(_ColorFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    else:
        console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    root.addHandler(console)

    # ── 文件 handler（可选） ──
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        root.addHandler(file_handler)

    # ── 第三方库降噪 ──
    for name, lvl in _NOISY_LOGGERS.items():
        logging.getLogger(name).setLevel(max(lvl, numeric_level))

    # ── uvicorn 日志接管 ──
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(console)
    uvicorn_logger.setLevel(numeric_level)

    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers.clear()
    uvicorn_error.setLevel(numeric_level)

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.setLevel(logging.WARNING)  # access log 降级，避免刷屏

    # ── 确认初始化完成 ──
    root.info(
        "Logging initialized: level=%s, handlers=%d, log_dir=%s",
        level, len(root.handlers), log_dir or "(console only)",
    )
