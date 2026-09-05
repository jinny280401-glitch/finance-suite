"""Provider observability — structured call logging for failure-layer attribution.

Each provider/runtime call emits a single-line JSON log with:
  request_id, domain, provider, endpoint, begin/end, latency_ms,
  outcome, exception_class, exception_message, row_count, field_count,
  fallback_used, runtime_identity

Outcome taxonomy (9 values):
  SUCCESS_WITH_DATA  — provider returned non-empty data
  VALID_EMPTY        — provider succeeded but returned empty result
  TIMEOUT            — call exceeded timeout threshold
  NETWORK_ERROR      — network-layer failure (ProxyError, ConnectionError, DNS, etc.)
  SESSION_ERROR      — session/credential/auth failure
  PROVIDER_ERROR     — provider returned error response (HTTP 4xx/5xx, API error)
  ADAPTER_ERROR      — adapter-layer failure (KeyError, TypeError, parameter mismatch)
  MAPPING_ERROR      — data exists but field mapping failed
  UNKNOWN_ERROR      — could not safely classify

Sensitive data (credentials, tokens, full payloads) is NEVER logged.

Usage:
  from scripts.provider_observability import (
      get_request_id, set_request_id, log_provider_call, classify_exception,
      ProviderOutcome,
  )

  # At entry point (stock_analysis / wind_query):
  set_request_id(str(uuid.uuid4()))

  # Inside each provider function:
  started = time.monotonic()
  outcome = None; exc_class = None; exc_msg = None
  try:
      result = provider_call()
      outcome = 'SUCCESS_WITH_DATA' if result else 'VALID_EMPTY'
      return result
  except Exception as e:
      exc_class = type(e).__name__
      exc_msg = str(e)[:200]
      outcome = classify_exception(e)
      return None
  finally:
      log_provider_call(
          domain='capital_flow', provider='akshare',
          endpoint='stock_individual_fund_flow',
          started_at=started, outcome=outcome,
          exception_class=exc_class, exception_message=exc_msg,
          row_count=row_count, field_count=field_count,
      )
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from typing import Any

logger = logging.getLogger(__name__)

# ---- request_id context (propagates through ThreadPoolExecutor) ----
_request_id: ContextVar[str] = ContextVar("provider_request_id", default="")


def set_request_id(rid: str) -> None:
    """Set request correlation ID for the current context."""
    _request_id.set(rid)


def get_request_id() -> str:
    """Get request correlation ID, or generate a new one if not set."""
    rid = _request_id.get()
    if not rid:
        rid = str(uuid.uuid4())
        _request_id.set(rid)
    return rid


# ---- Outcome classification ----

# Exception class name → outcome mapping.
# Conservative: only map clear signal patterns. Ambiguous → UNKNOWN_ERROR.
_NETWORK_EXC = frozenset({
    "ProxyError", "ConnectionError", "ConnectionRefusedError",
    "ConnectionResetError", "ConnectTimeout", "ConnectTimeoutError",
    "SSLError", "SSLCertVerificationError", "RemoteDisconnected",
    "MaxRetryError", "NewConnectionError", "DNSError", "URLError",
    "SocketError", "gaierror", "BrokenPipeError",
})
_SESSION_EXC = frozenset({
    "AuthenticationError", "AuthError", "UnauthorizedError",
    "TokenExpiredError", "CredentialError",
})
_PROVIDER_EXC = frozenset({
    "HTTPError", "BadRequest", "ServerError", "InternalServerError",
    "RateLimitError", "TooManyRedirects", "ServiceUnavailable",
    "GatewayTimeout",
})
_ADAPTER_EXC = frozenset({
    "KeyError", "TypeError", "AttributeError", "IndexError",
    "LookupError", "ValueError",
})
_MAPPING_EXC = frozenset({
    "FieldNotFound", "ColumnNotFound", "MissingColumnError",
})


def classify_exception(exc: BaseException) -> str:
    """Classify an exception into one of the 9 outcome categories.

    Prefer UNKNOWN_ERROR over an incorrect classification.
    Only returns NETWORK_ERROR, SESSION_ERROR, PROVIDER_ERROR,
    ADAPTER_ERROR, MAPPING_ERROR, TIMEOUT, or UNKNOWN_ERROR.
    """
    name = type(exc).__name__
    msg = str(exc)[:500].lower()

    # TIMEOUT check first — explicit timeout signals
    if "timeout" in name.lower() or "timeout" in msg:
        return "TIMEOUT"

    if name in _NETWORK_EXC:
        return "NETWORK_ERROR"
    if name in _SESSION_EXC:
        return "SESSION_ERROR"
    if name in _PROVIDER_EXC:
        return "PROVIDER_ERROR"
    if name in _ADAPTER_EXC:
        return "ADAPTER_ERROR"
    if name in _MAPPING_EXC:
        return "MAPPING_ERROR"

    # Keyword fallback for exceptions whose class name isn't in the frozen sets
    # but whose message contains strong network/auth signals.
    # Network keywords
    if any(kw in msg for kw in ("proxyerror", "proxy error", "connection refused",
                                  "connection reset", "no route to host",
                                  "name or service not known", "tls", "ssl",
                                  "certificate", "max retries exceeded",
                                  "failed to establish a new connection")):
        return "NETWORK_ERROR"

    # Auth/session keywords
    if any(kw in msg for kw in ("authentication failed", "unauthorized",
                                  "token expired", "invalid api key",
                                  "credential", "not logged in")):
        return "SESSION_ERROR"

    return "UNKNOWN_ERROR"


# ---- Runtime identity ----

def _get_runtime_identity() -> str:
    """Best-effort deployment identity. Returns git commit or 'unknown'."""
    # Check env var first (set at deploy time)
    env_id = os.environ.get("FS_DEPLOY_VERSION") or os.environ.get("DEPLOY_VERSION")
    if env_id:
        return env_id
    return "unknown"


# ---- Logging ----

def log_provider_call(
    *,
    domain: str,
    provider: str,
    endpoint: str,
    started_at: float,
    outcome: str,
    exception_class: str | None = None,
    exception_message: str | None = None,
    row_count: int | None = None,
    field_count: int | None = None,
    fallback_used: bool = False,
) -> None:
    """Emit a single-line JSON log for one provider/runtime call.

    Args:
        domain: Trust domain (financials, valuation, capital_flow, realtime, etc.)
        provider: Provider name (wind, tushare, joinquant, akshare, tencent)
        endpoint: Specific function/API called
        started_at: time.monotonic() value from call start
        outcome: One of the 9 outcome strings
        exception_class: type(e).__name__ if exception occurred
        exception_message: str(e)[:200] if exception occurred
        row_count: len(df) if result is a DataFrame
        field_count: len(df.columns) if result is a DataFrame
        fallback_used: True if this call is in a fallback chain
    """
    now = time.monotonic()
    latency_ms = round((now - started_at) * 1000)

    record = {
        "request_id": get_request_id(),
        "domain": domain,
        "provider": provider,
        "endpoint": endpoint,
        "begin_at": _ts(started_at),
        "end_at": _ts(now),
        "latency_ms": latency_ms,
        "outcome": outcome,
        "fallback_used": fallback_used,
        "runtime_identity": _get_runtime_identity(),
    }
    if exception_class:
        record["exception_class"] = exception_class
    if exception_message:
        record["exception_message"] = exception_message[:200]
    if row_count is not None:
        record["row_count"] = row_count
    if field_count is not None:
        record["field_count"] = field_count

    logger.info(json.dumps(record, ensure_ascii=False))


# Timestamp cache — time.monotonic doesn't map to wall clock, so we
# capture datetime.now() once per process and compute offsets.
_monotonic_base: float = time.monotonic()
_wall_clock_base: float = time.time()


def _ts(monotonic_val: float) -> str:
    """Convert time.monotonic() to ISO timestamp string."""
    offset = monotonic_val - _monotonic_base
    wall = _wall_clock_base + offset
    # Format as ISO without microseconds for compactness
    import datetime
    dt = datetime.datetime.fromtimestamp(wall, tz=datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}" + "Z"
