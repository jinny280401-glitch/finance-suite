#!/usr/bin/env python3
"""Provider-level smoke for the Choice shadow provider.

The smoke uses local fixtures only. It does not call Choice MCP, the network,
stock_data.py, prompts, API routes, or frontend code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from choice_provider import normalize_choice_table


ALLOWED_CONTRACT_STATUSES = {"success", "partial", "failure"}
FORBIDDEN_ALLOWED_USE = {
    "short_term_trade_signal",
    "capital_flow",
    "position_advice",
    "valuation_conclusion",
    "buy_sell_action",
}
REQUIRED_BLOCKED_FIELDS = {
    "short_term_trade_signal",
    "capital_flow",
    "technical_level",
    "position_advice",
    "buy_sell_action",
    "valuation_conclusion",
}
MAPPING_BLOCKED_FIELDS = {
    "resolved_code",
    "resolved_name",
    "code_dependent_fields",
}


def _success_raw() -> dict[str, Any]:
    return {
        "data": [
            {
                "columns": ["比亚迪(002594.SZ)", "2026-07-03"],
                "items": [["A股合计", "54.34亿股"], ["总资产", "8000亿元"]],
                "sheetName": "比亚迪(002594.SZ)的A股合计",
            }
        ]
    }


def _partial_raw() -> dict[str, Any]:
    return {
        "data": [
            {
                "columns": ["比亚迪(002594.SZ)"],
                "items": [["A股合计", "54.34亿股"]],
                "sheetName": "比亚迪(002594.SZ)的A股合计",
            }
        ]
    }


def _failure_raw() -> dict[str, Any]:
    return {
        "data": [
            {
                "columns": ["比亚迪(002594.SZ)", "2026-07-03"],
                "sheetName": "比亚迪(002594.SZ)的A股合计",
            }
        ]
    }


def _assert(condition: bool, message: str, assertions: list[dict[str, Any]]) -> None:
    assertions.append({"assertion": message, "passed": bool(condition)})
    if not condition:
        raise AssertionError(message)


def _run_case(name: str, raw: dict[str, Any], expected_contract_status: str, expected_mapping_status: str) -> dict[str, Any]:
    result = normalize_choice_table(raw, symbol="002594.SZ")
    qc = result.get("_qc") or {}
    mapping_guard = qc.get("mapping_guard") or {}
    assertions: list[dict[str, Any]] = []

    _assert(qc.get("status") == expected_contract_status, f"{name}: _qc.status is {expected_contract_status}", assertions)
    _assert(qc.get("status") in ALLOWED_CONTRACT_STATUSES, f"{name}: _qc.status is lowercase contract status", assertions)
    _assert(mapping_guard.get("status") == expected_mapping_status, f"{name}: mapping_guard.status is {expected_mapping_status}", assertions)
    _assert(mapping_guard.get("status") not in ALLOWED_CONTRACT_STATUSES, f"{name}: mapping_guard internal verdict does not pollute _qc.status", assertions)
    _assert(result.get("provider") == "choice" or expected_contract_status == "failure", f"{name}: provider is choice when usable", assertions)
    _assert(result.get("provider_tier") == 1 or expected_contract_status == "failure", f"{name}: provider_tier is numeric tier 1 when usable", assertions)
    _assert("provider_mode" in qc and "provider_mode" not in result.get("data", {}), f"{name}: provider_mode stays in qc/_qc", assertions)
    _assert(REQUIRED_BLOCKED_FIELDS.issubset(set(qc.get("blocked_fields") or [])), f"{name}: blocked_fields cover restricted conclusions", assertions)

    if expected_contract_status == "partial":
        allowed_use = set(qc.get("allowed_use") or [])
        _assert(allowed_use == {"basic_fundamental_snapshot"}, f"{name}: PARTIAL only allows basic_fundamental_snapshot", assertions)
        _assert(not (allowed_use & FORBIDDEN_ALLOWED_USE), f"{name}: PARTIAL forbids short-term/capital/position/valuation uses", assertions)

    if expected_contract_status == "failure":
        _assert(qc.get("allowed_use") == [], f"{name}: failure allowed_use is empty", assertions)
        _assert(MAPPING_BLOCKED_FIELDS.issubset(set(qc.get("blocked_fields") or [])), f"{name}: failure blocks mapping-dependent fields", assertions)

    return {
        "case": name,
        "input_shape": result.get("_qc", {}).get("raw_shape"),
        "provider": result.get("provider"),
        "provider_tier": result.get("provider_tier"),
        "provider_mode": qc.get("provider_mode"),
        "_qc.status": qc.get("status"),
        "mapping_guard.status": mapping_guard.get("status"),
        "allowed_use": qc.get("allowed_use"),
        "blocked_fields": qc.get("blocked_fields"),
        "sample": result,
        "assertions": assertions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Path to write JSON smoke evidence.")
    args = parser.parse_args()

    cases = [
        _run_case("success", _success_raw(), "success", "PASS"),
        _run_case("partial", _partial_raw(), "partial", "PARTIAL"),
        _run_case("failure", _failure_raw(), "failure", "FAIL"),
    ]
    payload = {
        "scope": "choice_provider.py provider-level smoke",
        "network_called": False,
        "choice_mcp_called": False,
        "stock_data_connected": False,
        "prompt_api_frontend_touched": False,
        "cases": cases,
        "verdict": "PASS",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": "PASS", "out": str(out), "cases": [case["case"] for case in cases]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
