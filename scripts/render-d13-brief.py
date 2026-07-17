#!/usr/bin/env python3
"""
render-d13-brief
================

CC-side half of the DRIFT-01 fix (2026-07-16/17): Codex (Intelligence Layer)
writes docs/d13_handoff_latest.json; this script (Display Layer) validates
it against the v1 schema and, only if valid, renders
d13_morning_brief.template.html into d13_morning_brief.html.

Schema doc: docs/d13_handoff_schema_v1.md
Design basis: project_intelligence_loop_v1 — "Codex 产 handoff.json,
CC 做 Trust Check + Template Render (schema 不合格拒渲染,不修内容)".

On validation failure: do NOT render, do NOT guess-fill, do NOT touch
yesterday's d13_morning_brief.html. Print every failing field to stderr
and exit non-zero. This mirrors brief-payload-builder.py's fail-safe
exit-code contract (0/1/2) with its own codes below.

Exit codes:
    0  rendered fresh handoff
    1  handoff missing (no JSON found)
    2  handoff invalid (schema violation — see stderr for details)

No network access. No third-party dependencies. Stdlib only — this
project intentionally avoids adding jsonschema as a dependency for a
single-file validator.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path.home() / "Documents" / "New project 6"
_DEFAULT_HANDOFF = PROJECT_ROOT / "docs" / "d13_handoff_latest.json"
TEMPLATE_PATH = PROJECT_ROOT / "d13_morning_brief.template.html"
OUTPUT_PATH = PROJECT_ROOT / "d13_morning_brief.html"

# Resolved at runtime — may be overridden via --handoff
HANDOFF_PATH = _DEFAULT_HANDOFF

_TONES = {"up", "down", "flat"}
_CONFIDENCE = {"HIGH", "MEDIUM", "PARTIAL"}
_OBS_TAGS = {"OBS-01", "OBS-02", "OBS-03"}


# ── Validation ───────────────────────────────────────────────────────────
def validate(data: Any, window: str = "morning") -> list[str]:
    """Return a list of human-readable error strings. Empty list = valid.

    window='morning': strict 4/3/3/3/3 counts (existing contract).
    window='midday'|'close': relaxed minimums (1 per array), caps at template max.
    """
    errors: list[str] = []
    strict = window == "morning"
    min_sections = 3 if strict else 0  # midday/close: empty sections OK
    min_drivers = 4 if strict else 1

    def require_str(obj: dict, key: str, allow_empty: bool = False, parent: str = "") -> None:
        path = f"{parent}.{key}" if parent else key
        if key not in obj:
            errors.append(f"missing required field: {path}")
            return
        v = obj[key]
        if not isinstance(v, str):
            errors.append(f"{path}: expected string, got {type(v).__name__}")
        elif not allow_empty and v.strip() == "":
            errors.append(f"{path}: must not be empty")

    if not isinstance(data, dict):
        return [f"handoff root must be an object, got {type(data).__name__}"]

    require_str(data, "date")
    if isinstance(data.get("date"), str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["date"]):
        errors.append("date: must match YYYY-MM-DD")

    require_str(data, "generated_at")
    require_str(data, "confidence")
    if data.get("confidence") not in _CONFIDENCE:
        errors.append(f"confidence: must be one of {sorted(_CONFIDENCE)}, got {data.get('confidence')!r}")

    for key in ("eyebrow_mode", "time_cst", "use_tag", "drivers_label",
                "h1_line_a", "h1_accent", "header_sub", "verdict", "footer_use"):
        require_str(data, key)
    require_str(data, "h1_line_b", allow_empty=True)

    # drivers: 4 for morning, 1–4 for midday/close (template has max 4 seats)
    drivers = data.get("drivers")
    if not isinstance(drivers, list):
        errors.append("drivers: must be an array")
    elif len(drivers) < min_drivers:
        errors.append(f"drivers: must have at least {min_drivers} item(s), got {len(drivers)}")
    elif len(drivers) > 4:
        errors.append(f"drivers: at most 4 items (template seats), got {len(drivers)}")
    else:
        for i, d in enumerate(drivers, start=1):
            p = f"drivers[{i}]"
            if not isinstance(d, dict):
                errors.append(f"{p}: must be an object")
                continue
            require_str(d, "key", parent=p)
            require_str(d, "value", parent=p)
            require_str(d, "unit", allow_empty=True, parent=p)
            require_str(d, "delta", allow_empty=True, parent=p)
            require_str(d, "desc", parent=p)
            if d.get("delta", "").strip():
                if d.get("tone") not in _TONES:
                    errors.append(f"{p}.tone: required when delta is non-empty, must be one of {sorted(_TONES)}")

    # impact / opportunities / risks / watchlist: exactly 3 for morning, 1–3 for midday/close
    def require_section(field: str, item_fields: dict[str, bool]) -> None:
        items = data.get(field)
        if not isinstance(items, list):
            errors.append(f"{field}: must be an array")
            return
        if len(items) < min_sections:
            errors.append(f"{field}: must have at least {min_sections} item(s), got {len(items)}")
            return
        if len(items) > 3:
            errors.append(f"{field}: at most 3 items, got {len(items)}")
            return
        for i, item in enumerate(items, start=1):
            p = f"{field}[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{p}: must be an object")
                continue
            for fkey, allow_empty in item_fields.items():
                require_str(item, fkey, allow_empty=allow_empty, parent=p)

    # For non-morning windows, opportunity driver/observe may be auto-filled
    opp_allow_empty = not strict
    require_section("impact", {"target": False, "body": False})
    require_section("opportunities", {"title": False, "driver": opp_allow_empty, "observe": opp_allow_empty})
    require_section("risks", {"title": False, "body": False})
    require_section("watchlist", {"text": False, "tag": False})

    watchlist = data.get("watchlist")
    if isinstance(watchlist, list):
        for i, item in enumerate(watchlist, start=1):
            if isinstance(item, dict):
                tag = item.get("tag", "")
                if strict and tag not in _OBS_TAGS:
                    errors.append(f"watchlist[{i}].tag: must be one of {sorted(_OBS_TAGS)}, got {tag!r}")
                elif not strict and not tag.strip():
                    errors.append(f"watchlist[{i}].tag: must not be empty")

    ticker = data.get("ticker_items")
    if not isinstance(ticker, list) or len(ticker) < 1:
        errors.append("ticker_items: must be a non-empty array of strings")
    elif not all(isinstance(t, str) and t.strip() for t in ticker):
        errors.append("ticker_items: every item must be a non-empty string")

    return errors


# ── Content formatting ──────────────────────────────────────────────────
def _inline_format(text: str) -> str:
    """Escape HTML, then apply the two allowed minimal-markdown marks.

    Escaping first means **/* typed by Codex can't smuggle real markup —
    only the exact **bold** / *italic* patterns this function re-adds
    produce tags.
    """
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return escaped


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


# ── Rendering ────────────────────────────────────────────────────────────
def render(data: dict, template: str) -> str:
    slots: dict[str, str] = {
        "DATE": _esc(data["date"]),
        "TIME_CST": _esc(data["time_cst"]),
        "EYEBROW_MODE": _esc(data["eyebrow_mode"]),
        "H1_LINE_A": _esc(data["h1_line_a"]),
        "H1_ACCENT": _esc(data["h1_accent"]),
        "H1_LINE_B": _esc(data["h1_line_b"]),
        "HEADER_SUB": _esc(data["header_sub"]),
        "CONFIDENCE": _esc(data["confidence"]),
        "USE_TAG": _esc(data["use_tag"]),
        "VERDICT": _esc(data["verdict"]),
        "DRIVERS_LABEL": _esc(data["drivers_label"]),
        "FOOTER_USE": _esc(data["footer_use"]),
    }

    for i, d in enumerate(data["drivers"], start=1):
        slots[f"DRIVER_{i}_KEY"] = _esc(d["key"])
        slots[f"DRIVER_{i}_VAL"] = _esc(d["value"])
        slots[f"DRIVER_{i}_DESC"] = _esc(d["desc"])
        # Empty unit/delta -> drop the whole inner span, not just the token
        # (matches template's own authoring rule: never leave an empty tag).
        slots[f"DRIVER_{i}_UNIT_SPAN"] = (
            f'<span class="unit">{_esc(d["unit"])}</span>' if d.get("unit", "").strip() else ""
        )
        slots[f"DRIVER_{i}_DELTA_SPAN"] = (
            f'<span class="delta {_esc(d.get("tone", "flat"))}">{_esc(d["delta"])}</span>'
            if d.get("delta", "").strip() else ""
        )

    for i, item in enumerate(data["impact"], start=1):
        slots[f"IMPACT_{i}_TARGET"] = _inline_format(item["target"])
        slots[f"IMPACT_{i}_BODY"] = _inline_format(item["body"])

    for i, item in enumerate(data["opportunities"], start=1):
        slots[f"OPP_{i}_TITLE"] = _inline_format(item["title"])
        slots[f"OPP_{i}_DRIVER"] = _inline_format(item["driver"])
        slots[f"OPP_{i}_OBSERVE"] = _inline_format(item["observe"])

    for i, item in enumerate(data["risks"], start=1):
        slots[f"RISK_{i}_TITLE"] = _inline_format(item["title"])
        slots[f"RISK_{i}_BODY"] = _inline_format(item["body"])

    for i, item in enumerate(data["watchlist"], start=1):
        slots[f"WATCH_{i}_TEXT"] = _inline_format(item["text"])
        slots[f"WATCH_{i}_TAG"] = _esc(item["tag"])

    ticker_html = "\n        ".join(f'<span class="tk">{_esc(t)}</span>' for t in data["ticker_items"])
    slots["TICKER_ITEMS"] = ticker_html

    # Pad driver slots — template has 4 seats, but midday/close may use fewer
    for i in range(len(data["drivers"]) + 1, 5):
        slots[f"DRIVER_{i}_KEY"] = ""
        slots[f"DRIVER_{i}_VAL"] = ""
        slots[f"DRIVER_{i}_DESC"] = ""
        slots[f"DRIVER_{i}_UNIT_SPAN"] = ""
        slots[f"DRIVER_{i}_DELTA_SPAN"] = ""

    # Pad section slots — template has 3 seats each
    for field, prefix in [("impact", "IMPACT"), ("opportunities", "OPP"), ("risks", "RISK"), ("watchlist", "WATCH")]:
        items = data.get(field, [])
        for i in range(len(items) + 1, 4):
            if field == "impact":
                slots[f"{prefix}_{i}_TARGET"] = ""
                slots[f"{prefix}_{i}_BODY"] = ""
            elif field == "opportunities":
                slots[f"{prefix}_{i}_TITLE"] = ""
                slots[f"{prefix}_{i}_DRIVER"] = ""
                slots[f"{prefix}_{i}_OBSERVE"] = ""
            elif field == "risks":
                slots[f"{prefix}_{i}_TITLE"] = ""
                slots[f"{prefix}_{i}_BODY"] = ""
            elif field == "watchlist":
                slots[f"{prefix}_{i}_TEXT"] = ""
                slots[f"{prefix}_{i}_TAG"] = ""

    out = template
    # Driver unit/delta spans are hardcoded in the template as
    # <span class="unit">{{DRIVER_n_UNIT}}</span><span class="delta {{DRIVER_n_TONE}}">{{DRIVER_n_DELTA}}</span>
    # — replace each *whole* span pair via the _SPAN slots computed above,
    # rather than filling {{DRIVER_n_UNIT}}/{{DRIVER_n_TONE}}/{{DRIVER_n_DELTA}}
    # individually, so an empty unit/delta drops the tag instead of leaving it blank.
    for i in range(1, 5):
        out = re.sub(
            r'<span class="unit">\{\{DRIVER_' + str(i) + r'_UNIT\}\}</span>'
            r'<span class="delta \{\{DRIVER_' + str(i) + r'_TONE\}\}">\{\{DRIVER_' + str(i) + r'_DELTA\}\}</span>',
            slots.pop(f"DRIVER_{i}_UNIT_SPAN", "") + slots.pop(f"DRIVER_{i}_DELTA_SPAN", ""),
            out,
        )

    for key, value in slots.items():
        out = out.replace("{{" + key + "}}", value)

    return out


def strip_comment_header(html_text: str) -> str:
    """Drop the build-time <!-- ... --> guidance block right after <!DOCTYPE html>."""
    return re.sub(r"(<!DOCTYPE html>\s*)<!--.*?-->\s*", r"\1", html_text, count=1, flags=re.DOTALL)


# ── Contract mapping (midday/close → template slots) ────────────────────
def map_contract(data: dict, window: str) -> dict:
    """Map window-specific handoff contracts to template-compatible structure.

    Morning v1 passes through unchanged (it already matches the template).
    Midday (d13-midday-handoff-v1) and Close (d13-close-handoff-v1) use
    different field names — this function translates them so the existing
    render() engine can fill the same template slots.
    """
    if window == "morning":
        return data

    # ── Shared derived fields ──────────────────────────────────────────
    eyeborw = {"midday": "午间验证", "close": "收盘验证"}.get(window, "")
    qc = data.get("qc", {})
    freshness = qc.get("freshness", "")
    sources = ", ".join(qc.get("sources", [])) if isinstance(qc.get("sources"), list) else ""
    actuals = data.get("actuals", []) if isinstance(data.get("actuals"), list) else []
    comparisons = data.get("comparisons", []) if isinstance(data.get("comparisons"), list) else []

    out: dict = {
        "date": data.get("date", ""),
        "generated_at": data.get("generated_at", ""),
        "confidence": data.get("confidence", "MEDIUM"),
        "time_cst": data.get("as_of", data.get("time_cst", "")),
        "eyebrow_mode": eyeborw,
        "use_tag": f"数据源: {sources}" if sources else "Loop验证",
        "drivers_label": f"· {window} snapshot · {freshness}" if freshness else f"· {window} snapshot",
        "h1_line_a": data.get("market_summary", data.get("day_summary", "")),
        "h1_accent": data.get("deviation_summary", "")
                     or (f"{sum(1 for c in comparisons if isinstance(c, dict) and c.get('result') == 'DEVIATED')}项偏差"
                         if any(isinstance(c, dict) and c.get("result") == 'DEVIATED' for c in comparisons)
                         else "验证中"),
        "h1_line_b": "",
        "header_sub": f"QC: {qc.get('status', 'unknown')} · 置信度: {data.get('confidence', 'MEDIUM')}",
        "verdict": data.get("deviation_summary", data.get("day_summary", data.get("market_summary", "")))
                   or (f"{sum(1 for c in comparisons if isinstance(c, dict) and c.get('result') == 'CONFIRMED')}确认/{sum(1 for c in comparisons if isinstance(c, dict) and c.get('result') == 'DEVIATED')}偏差"
                       if len(comparisons) > 0
                       else "验证完成"),
        "footer_use": data.get("allowed_use", "仅用于宏观观察，不构成交易建议"),
    }

    # ── actuals → drivers ──────────────────────────────────────────────
    drivers = []
    for a in actuals if isinstance(actuals, list) else []:
        if not isinstance(a, dict):
            continue
        tone = "flat"
        change = a.get("actual_change", "")
        if isinstance(change, str):
            if change.startswith("+") or "涨" in change or "up" in change.lower():
                tone = "up"
            elif change.startswith("-") or "跌" in change or "down" in change.lower():
                tone = "down"
        drivers.append({
            "key": a.get("key", ""),
            "value": str(a.get("actual_value", "")),
            "unit": "",
            "delta": change,
            "tone": tone,
            "desc": f"预期: {a.get('expected_value', '')} ({a.get('expected_tone', '')}), 来源: {a.get('source', '')}",
        })
    out["drivers"] = drivers

    # ── comparisons → impact ───────────────────────────────────────────
    impacts = []
    for c in comparisons if isinstance(comparisons, list) else []:
        if not isinstance(c, dict):
            continue
        result = c.get("result", "INCONCLUSIVE")
        emoji = {"CONFIRMED": "✓", "DEVIATED": "⚠", "INCONCLUSIVE": "?"}.get(result, "")
        impacts.append({
            "target": f"{emoji} {c.get('key', '')} — {result}",
            "body": c.get("reason", ""),
        })
    out["impact"] = impacts

    # ── window-specific → opportunities / risks ────────────────────────
    if window == "midday":
        ops = []
        rs = []
        for c in comparisons if isinstance(comparisons, list) else []:
            if not isinstance(c, dict):
                continue
            if c.get("result") == "CONFIRMED":
                ops.append({"title": c.get("key", ""), "driver": c.get("reason", ""), "observe": "预期验证通过"})
            elif c.get("result") == "DEVIATED":
                rs.append({"title": c.get("key", ""), "body": c.get("reason", "")})
        out["opportunities"] = ops
        out["risks"] = rs

    elif window == "close":
        fb = data.get("feedback", {}) if isinstance(data.get("feedback"), dict) else {}
        patterns = fb.get("confirmed_patterns", [])
        out["opportunities"] = [
            {"title": p, "driver": p, "observe": "全天验证确认"}
            for p in (patterns if isinstance(patterns, list) else [])
        ]
        missed = fb.get("missed_assumptions", [])
        unresolved = fb.get("unresolved_items", [])
        all_risks = (missed if isinstance(missed, list) else []) + (unresolved if isinstance(unresolved, list) else [])
        out["risks"] = [{"title": r, "body": r} for r in all_risks[:3]]  # template max 3 seats

    # ── watchlist ──────────────────────────────────────────────────────
    wl = data.get("watchlist", [])
    if wl and isinstance(wl, list) and len(wl) > 0 and isinstance(wl[0], str):
        out["watchlist"] = [{"text": w, "tag": f"{'MID' if window == 'midday' else 'CLS'}-{i+1:02d}"} for i, w in enumerate(wl)]
    elif window == "close":
        # Close contract: watchlist optional; fallback to tomorrow_context
        fb_close = data.get("feedback", {}) if isinstance(data.get("feedback"), dict) else {}
        tc = fb_close.get("tomorrow_context", [])
        if isinstance(tc, list) and len(tc) > 0:
            # Flatten: each item may itself be a string or a list of strings
            flat: list[str] = []
            for item in tc:
                if isinstance(item, str):
                    flat.append(item)
                elif isinstance(item, list):
                    flat.extend(str(x) for x in item)
            out["watchlist"] = [{"text": t, "tag": f"CLS-{i+1:02d}"} for i, t in enumerate(flat[:3])]
        elif isinstance(tc, str) and tc.strip():
            out["watchlist"] = [{"text": tc.strip(), "tag": "CLS-01"}]
        else:
            out["watchlist"] = []
    else:
        out["watchlist"] = wl if isinstance(wl, list) else []

    # ── ticker ─────────────────────────────────────────────────────────
    ticker = []
    for a in actuals if isinstance(actuals, list) else []:
        if isinstance(a, dict):
            ticker.append(f"{a.get('key','')} {a.get('actual_value','')}")
    out["ticker_items"] = ticker if ticker else ["数据待更新"]

    return out


# ── Entry ────────────────────────────────────────────────────────────────
def main() -> int:
    global HANDOFF_PATH

    parser = argparse.ArgumentParser(description="Render D13 brief from handoff JSON")
    parser.add_argument(
        "--handoff",
        type=Path,
        default=_DEFAULT_HANDOFF,
        help=f"Path to handoff JSON (default: {_DEFAULT_HANDOFF})",
    )
    parser.add_argument(
        "--window",
        choices=["morning", "midday", "close"],
        default="morning",
        help="Window: morning (strict 4/3/3/3/3), midday/close (relaxed 1–4/1–3)",
    )
    args = parser.parse_args()
    HANDOFF_PATH = args.handoff

    if not HANDOFF_PATH.is_file():
        print(f"[render-d13-brief] handoff missing: {HANDOFF_PATH}", file=sys.stderr)
        return 1

    try:
        raw = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[render-d13-brief] handoff is not valid JSON: {e}", file=sys.stderr)
        return 2

    # Map window-specific contracts to template-compatible structure
    data = map_contract(raw, window=args.window)

    errors = validate(data, window=args.window)
    if errors:
        print(f"[render-d13-brief] handoff failed validation ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print("[render-d13-brief] REFUSING to render. Yesterday's d13_morning_brief.html left untouched.", file=sys.stderr)
        return 2

    if not TEMPLATE_PATH.is_file():
        print(f"[render-d13-brief] template missing: {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    template = strip_comment_header(TEMPLATE_PATH.read_text(encoding="utf-8"))
    rendered = render(data, template)

    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", rendered)
    if remaining:
        print(f"[render-d13-brief] internal error: unfilled slots remain: {sorted(set(remaining))}", file=sys.stderr)
        print("[render-d13-brief] REFUSING to write partially-rendered output.", file=sys.stderr)
        return 2

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"[render-d13-brief] rendered {HANDOFF_PATH.name} -> {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
