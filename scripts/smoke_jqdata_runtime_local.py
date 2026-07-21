#!/usr/bin/env python3
"""Local non-paid JQData runtime smoke.

This smoke only verifies importability and credential key presence. It must not
authenticate, query JQData, or call any paid API surface.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any


ARTIFACT_PATH = Path("/tmp/jqdata_runtime_smoke_20260705.json")
REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_KEYS = (
    "JQ_USERNAME",
    "JQ_PASSWORD",
    "JQDATA_USERNAME",
    "JQDATA_PASSWORD",
)


def _load_env_presence() -> dict[str, bool]:
    """Return credential key presence without returning values."""
    values: dict[str, str] = {key: os.environ.get(key, "") for key in REQUIRED_KEYS}
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            if key in values and not values[key]:
                values[key] = value.strip()
    return {key: bool(values.get(key)) for key in REQUIRED_KEYS}


def _import_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {
            "ok": True,
            "module": name,
            "origin": getattr(module, "__file__", None),
            "error_type": None,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - smoke must classify import failures.
        return {
            "ok": False,
            "module": name,
            "origin": None,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    jqdatasdk_import = _import_module("jqdatasdk")
    wrapper_import = _import_module("scripts.jqdata_fetch")
    credential_presence = _load_env_presence()
    credential_present = all(credential_presence.values())

    if not jqdatasdk_import["ok"]:
        failure_class = "sdk_missing"
    elif not wrapper_import["ok"]:
        failure_class = "wrapper_import_failed"
    elif not credential_present:
        failure_class = "credential_missing"
    else:
        failure_class = "success"

    result = {
        "python_path": sys.executable,
        "repo_root": str(REPO_ROOT),
        "jqdatasdk_import": jqdatasdk_import,
        "jqdata_fetch_import": wrapper_import,
        "credential_present": credential_present,
        "credential_key_presence": credential_presence,
        "failure_class": failure_class,
        "no_paid_query": True,
        "auth_executed": False,
        "query_executed": False,
    }

    ARTIFACT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if failure_class == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
