"""Choice MCP shadow provider.

This module only normalizes already-fetched Choice MCP table payloads into the
existing Finance Suite data contract. It does not call Choice MCP directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from finance_data_contract import build_response


CHOICE_PROVIDER = "choice"
CHOICE_PROVIDER_TIER = 1
CHOICE_PROVIDER_WINDOW = {"start": "2020-01-01", "end": "2099-12-31"}

BASIC_ALLOWED_USE = [
    "basic_fundamental_snapshot",
    "company_basic_reference",
    "historical_finance_reference",
]

RESTRICTED_ALLOWED_USE = [
    "basic_fundamental_snapshot",
]

DEFAULT_BLOCKED_FIELDS = [
    "realtime_price",
    "intraday_strength",
    "technical_level",
    "capital_flow",
    "northbound_flow",
    "main_fund_flow",
    "dragon_tiger_list",
    "volume_confirmation",
    "position_advice",
    "buy_sell_action",
    "valuation_conclusion",
    "short_term_trade_signal",
]

MAPPING_BLOCKED_FIELDS = [
    "resolved_code",
    "resolved_name",
    "code_dependent_fields",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _first_table(raw: dict[str, Any]) -> dict[str, Any] | None:
    data = raw.get("data") if isinstance(raw, dict) else None
    if not isinstance(data, list) or not data:
        return None
    table = data[0]
    return table if isinstance(table, dict) else None


def _extract_as_of(columns: list[Any]) -> str | None:
    if len(columns) < 2:
        return None
    value = columns[1]
    if value in (None, ""):
        return None
    return str(value)


def _raw_shape(raw: dict[str, Any]) -> dict[str, Any]:
    table = _first_table(raw)
    if table is None:
        return {
            "has_data": isinstance(raw, dict) and isinstance(raw.get("data"), list),
            "table_count": len(raw.get("data") or []) if isinstance(raw, dict) and isinstance(raw.get("data"), list) else 0,
            "has_columns": False,
            "has_items": False,
            "has_sheet_name": False,
        }
    return {
        "has_data": True,
        "table_count": len(raw.get("data") or []),
        "has_columns": isinstance(table.get("columns"), list),
        "has_items": isinstance(table.get("items"), list),
        "has_sheet_name": bool(table.get("sheetName")),
        "columns_count": len(table.get("columns") or []) if isinstance(table.get("columns"), list) else 0,
        "items_count": len(table.get("items") or []) if isinstance(table.get("items"), list) else 0,
    }


def _evaluate_mapping_guard(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate the minimal Choice table shape without inventing caller fields."""
    table = _first_table(raw)
    if table is None:
        return {
            "status": "FAIL",
            "reason": "Choice response must contain data[0] table.",
            "internal_verdict": "FAIL",
        }

    columns = table.get("columns")
    items = table.get("items")
    sheet_name = table.get("sheetName")
    missing = []
    if not isinstance(columns, list) or not columns:
        missing.append("columns")
    if not isinstance(items, list):
        missing.append("items")
    if not sheet_name:
        missing.append("sheetName")
    if missing:
        return {
            "status": "FAIL",
            "reason": f"Choice table missing required fields: {', '.join(missing)}.",
            "missing_fields": missing,
            "internal_verdict": "FAIL",
        }

    if len(columns) < 2:
        return {
            "status": "PARTIAL",
            "reason": "Choice table lacks an as_of/date column.",
            "missing_fields": ["as_of"],
            "internal_verdict": "PARTIAL",
        }

    if not items:
        return {
            "status": "PARTIAL",
            "reason": "Choice table has no data rows.",
            "missing_fields": ["items"],
            "internal_verdict": "PARTIAL",
        }

    return {
        "status": "PASS",
        "reason": None,
        "internal_verdict": "PASS",
    }


def _derive_allowed_use(raw: dict[str, Any], mapping_guard: dict[str, Any]) -> list[str]:
    del raw
    if mapping_guard.get("status") == "FAIL":
        return []
    if mapping_guard.get("status") == "PARTIAL":
        return list(RESTRICTED_ALLOWED_USE)
    return list(BASIC_ALLOWED_USE)


def _derive_blocked_fields(raw: dict[str, Any], mapping_guard: dict[str, Any]) -> list[str]:
    blocked = list(DEFAULT_BLOCKED_FIELDS)
    table = _first_table(raw)
    columns = table.get("columns") if table else []
    if not isinstance(columns, list) or _extract_as_of(columns) is None:
        blocked.append("as_of")
    if mapping_guard.get("status") == "FAIL":
        blocked.extend(MAPPING_BLOCKED_FIELDS)
    return list(dict.fromkeys(blocked))


def _contract_status(mapping_guard: dict[str, Any]) -> tuple[bool, str, str]:
    status = mapping_guard.get("status")
    if status == "PASS":
        return True, "success", "daily"
    if status == "PARTIAL":
        return True, "partial", "unknown"
    return False, "failure", "unavailable"


def normalize_choice_table(
    raw: dict[str, Any],
    symbol: str | None = None,
    data_type: str = "fundamental_snapshot",
) -> dict[str, Any]:
    """Normalize a mocked/read-only Choice MCP table response into build_response()."""
    mapping_guard = _evaluate_mapping_guard(raw)
    ok, status, freshness = _contract_status(mapping_guard)
    table = _first_table(raw)
    columns = table.get("columns") if table else []
    items = table.get("items") if table else []
    sheet_name = table.get("sheetName") if table else None
    as_of = _extract_as_of(columns if isinstance(columns, list) else [])
    raw_shape = _raw_shape(raw)
    blocked_fields = _derive_blocked_fields(raw, mapping_guard)
    allowed_use = _derive_allowed_use(raw, mapping_guard)
    provider_mode = "real" if ok else "fail"

    qc = {
        "status": status,
        "reason": mapping_guard.get("reason"),
        "sources": [CHOICE_PROVIDER] if ok else [],
        "blocked_fields": blocked_fields,
        "allowed_use": allowed_use,
        "mapping_guard": mapping_guard,
        "provider_window": CHOICE_PROVIDER_WINDOW,
        "raw_shape": raw_shape,
        "provider_mode": provider_mode,
        "missing_fields": mapping_guard.get("missing_fields", []),
        "missing_dimensions": mapping_guard.get("missing_fields", []),
        "completeness": 1.0 if status == "success" else 0.5 if status == "partial" else 0,
        "partial": status == "partial",
    }

    data = {
        "sheet_name": sheet_name,
        "columns": columns if isinstance(columns, list) else [],
        "items": items if isinstance(items, list) else [],
        "as_of": as_of,
        "raw_provider": "choice_mcp",
    }

    return build_response(
        ok=ok,
        symbol=symbol,
        data_type=data_type,
        provider=CHOICE_PROVIDER if ok else None,
        provider_tier=CHOICE_PROVIDER_TIER if ok else None,
        freshness=freshness,
        as_of=as_of or _utc_now_iso(),
        data=data,
        qc=qc,
    )
