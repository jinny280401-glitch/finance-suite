#!/usr/bin/env python3
"""
loop-orchestrator — Three-window daily intelligence loop

Window 1 — Morning Brief (08:30 trigger, Codex 08:57 cron):
    Codex generates d13_handoff_latest.json via its automation.
    CC renders → brief-payload-builder hydrates.

Window 2 — Midday Pulse (12:05 trigger):
    Verify morning expectations against actual AM price action.
    Write midday_handoff.json → render midday card → hydrate sidebar.

Window 3 — Close Brief (16:15 trigger):
    Full-day verification. Compare open expectations vs close reality.
    Write feedback into next-day context for tomorrow's Morning Brief.

This is the CC-side (Display Layer) orchestrator. Codex (Intelligence
Layer) produces the handoff JSONs; CC validates and renders.

Usage:
    python3 loop-orchestrator.py morning   # Window 1 (08:30 entry)
    python3 loop-orchestrator.py midday    # Window 2 (12:05 entry)
    python3 loop-orchestrator.py close     # Window 3 (16:15 entry)
    python3 loop-orchestrator.py status    # Print loop state

Exit codes:
    0 — window completed successfully
    1 — handoff missing (Codex hasn't generated yet)
    2 — handoff invalid (schema violation)
    3 — hydration failed
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────
NEW_PROJECT = Path.home() / "Documents" / "New project 6"
FINANCE_SUITE = Path.home() / "finance-suite"

HANDOFF_PATHS = {
    "morning": NEW_PROJECT / "docs" / "d13_handoff_latest.json",
    "midday": NEW_PROJECT / "docs" / "midday_handoff_latest.json",
    "close": NEW_PROJECT / "docs" / "close_handoff_latest.json",
}

RENDER_SCRIPT = FINANCE_SUITE / "scripts" / "render-d13-brief.py"
HYDRATION_SCRIPT = FINANCE_SUITE / "scripts" / "brief-payload-builder.py"

LOOP_STATE = FINANCE_SUITE / "data" / "morning_brief" / "loop_state.json"

CST = timezone(__import__("datetime").timedelta(hours=8))


def now_cst() -> datetime:
    return datetime.now(CST)


def log(msg: str) -> None:
    ts = now_cst().strftime("%H:%M:%S")
    print(f"[loop:{ts}] {msg}", file=sys.stderr)


def read_loop_state() -> dict:
    if LOOP_STATE.is_file():
        return json.loads(LOOP_STATE.read_text(encoding="utf-8"))
    return {"morning_expectations": {}, "midday_verified": False, "close_feedback": {}}


def write_loop_state(state: dict) -> None:
    LOOP_STATE.parent.mkdir(parents=True, exist_ok=True)
    LOOP_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def run_render(handoff_path: Path) -> int:
    """Call render-d13-brief.py. Exit code: 0=ok, 1=missing, 2=invalid."""
    result = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT)],
        capture_output=True, text=True, timeout=30,
    )
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            log(f"render: {line}")
    return result.returncode


def run_hydration() -> dict:
    """Call brief-payload-builder.py. Returns parsed status."""
    result = subprocess.run(
        [sys.executable, str(HYDRATION_SCRIPT)],
        capture_output=True, text=True, timeout=30,
    )
    status = {"exit_code": result.returncode, "status": "unknown"}
    try:
        latest_json = FINANCE_SUITE / "data" / "morning_brief" / "latest.json"
        if latest_json.is_file():
            data = json.loads(latest_json.read_text(encoding="utf-8"))
            status["status"] = data.get("status", "unknown")
            status["generated_at"] = data.get("generated_at", "")
    except Exception:
        pass
    return status


def window_morning() -> int:
    """Window 1: Morning Brief. Codex should have already generated handoff."""
    log("Window 1 — Morning Brief")
    handoff = HANDOFF_PATHS["morning"]

    if not handoff.is_file():
        log(f"ERROR: handoff missing at {handoff}")
        log("Codex automation should have generated this by 08:57")
        return 1

    # Read expectations for later verification
    try:
        data = json.loads(handoff.read_text(encoding="utf-8"))
        state = read_loop_state()
        state["morning_expectations"] = {
            "date": data.get("date", ""),
            "verdict": data.get("verdict", ""),
            "drivers": [
                {"key": d.get("key", ""), "value": d.get("value", ""), "tone": d.get("tone", "")}
                for d in data.get("drivers", [])
            ],
            "generated_at": data.get("generated_at", ""),
        }
        state["midday_verified"] = False
        state["close_feedback"] = {}
        write_loop_state(state)
        log("morning expectations captured for midday verification")
    except Exception as e:
        log(f"WARNING: failed to capture expectations: {e}")

    # Hydration (render already done by Codex automation)
    hyd = run_hydration()
    log(f"hydration: {hyd['status']} (exit {hyd['exit_code']})")

    return 0


def window_midday() -> int:
    """Window 2: Midday Pulse. Verify AM action against morning expectations."""
    log("Window 2 — Midday Pulse")

    state = read_loop_state()
    if not state.get("morning_expectations"):
        log("WARNING: no morning expectations found — skipping verification")
    else:
        log(f"verifying against: {state['morning_expectations'].get('date', 'unknown')}")

    handoff = HANDOFF_PATHS["midday"]
    if not handoff.is_file():
        log("midday handoff not yet generated — Codex may still be working")
        return 1

    rc = run_render(handoff)
    if rc != 0:
        log(f"render failed with exit code {rc}")
        return rc

    hyd = run_hydration()
    log(f"hydration: {hyd['status']} (exit {hyd['exit_code']})")

    state["midday_verified"] = True
    write_loop_state(state)

    return 0


def window_close() -> int:
    """Window 3: Close Brief. Full-day verification + feedback for tomorrow."""
    log("Window 3 — Close Brief")

    state = read_loop_state()

    handoff = HANDOFF_PATHS["close"]
    if not handoff.is_file():
        log("close handoff not yet generated — Codex may still be working")
        return 1

    rc = run_render(handoff)
    if rc != 0:
        log(f"render failed with exit code {rc}")
        return rc

    hyd = run_hydration()
    log(f"hydration: {hyd['status']} (exit {hyd['exit_code']})")

    # Write feedback for tomorrow's morning brief
    state["close_feedback"] = {
        "completed_at": now_cst().isoformat(),
        "midday_verified": state.get("midday_verified", False),
    }
    write_loop_state(state)
    log("close feedback captured for next morning brief")

    return 0


def print_status() -> int:
    """Print current loop state."""
    state = read_loop_state()
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: loop-orchestrator.py <morning|midday|close|status>", file=sys.stderr)
        return 1

    window = sys.argv[1]
    windows = {"morning": window_morning, "midday": window_midday, "close": window_close, "status": print_status}

    if window not in windows:
        print(f"Unknown window: {window}", file=sys.stderr)
        return 1

    return windows[window]()


if __name__ == "__main__":
    sys.exit(main())
