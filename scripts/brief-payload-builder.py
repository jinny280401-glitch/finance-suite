#!/usr/bin/env python3
"""
brief-payload-builder
=====================

Read the most recent D13 morning brief artifact (HTML preferred,
Markdown fallback) from
    ~/Documents/New project 6/d13_morning_brief.html
    ~/Documents/New project 6/docs/d13_*brief*.md
and emit a JSON payload + HTML copy under
    finance-suite/data/morning_brief/latest.json
    finance-suite/data/morning_brief/latest.html

Why HTML first: the d13 template HTML carries the four driver values
as standalone tokens inside ``.driver-val`` blocks, so regex extraction
is unambiguous. Markdown prose instead inverts multiple numbers
("PMI 从 50.0 回到 50.3") and pattern matching becomes fragile.

Three terminal states (also reflected in exit code):

    0  fresh   — most recent brief is < 24 h old
    1  stale   — most recent brief exists but is older
    2  empty   — no brief artifact found at all

No network access. No third-party dependencies. Stdlib only.

This script does NOT generate a brief; it only mirrors what the
Codex automation at ~/.codex/automations/d13-morning-brief already
produces. Hook this into the Codex prompt if you want it to run
automatically after each morning brief lands.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Configuration ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path.home() / "Documents" / "New project 6"
FINANCE_SUITE = Path.home() / "finance-suite"

DOCS_DIR = PROJECT_ROOT / "docs"
HTML_SOURCE = PROJECT_ROOT / "d13_morning_brief.html"

OUTPUT_DIR = FINANCE_SUITE / "data" / "morning_brief"
OUTPUT_JSON = OUTPUT_DIR / "latest.json"
OUTPUT_HTML = OUTPUT_DIR / "latest.html"

FRESH_WINDOW_HOURS = 24

# Order of preference: HTML → markdown. The HTML artifact carries the
# driver values as standalone tokens inside .driver-val blocks — much
# more reliable than prose markdown.
_DRIVER_ORDER: list[tuple[str, str]] = [
    ("pmi_official", "CN PMI 官方"),
    ("pmi_private", "CN PMI RatingDog"),
    ("brent", "Brent 油价"),
    ("us_jobs", "今晚关键事件"),
]


# ── Search for the newest d13 brief ───────────────────────────────────────
def find_latest_brief() -> Optional[Path]:
    """Pick the freshest available brief artifact (HTML preferred, MD fallback)."""
    if HTML_SOURCE.is_file():
        return HTML_SOURCE
    if DOCS_DIR.is_dir():
        candidates = sorted(
            (DOCS_DIR.glob("d13_*brief*.md")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return candidates[0]
    return None


# ── Parsing (HTML-first, Markdown fallback) ───────────────────────────────
# Capture each driver block's key label plus the *entire* .driver-val inner
# HTML (number + any delta/unit spans), so we can read both the value and the
# tone. We intentionally do NOT hardcode which four seats the card carries:
# the brief's data seats legitimately change day to day (PMI/Brent/jobs one
# day, index/FX/rates the next), so the parser emits whatever seats the HTML
# actually contains rather than a fixed canonical set.
_HTML_DRIVER_REGEX = re.compile(
    r'<div\s+class="driver-key">([^<]+)</div>\s*'
    r'<div\s+class="driver-val">(.*?)</div>',
    flags=re.IGNORECASE | re.DOTALL,
)

# delta class in the .driver-val span → mini-bar tone.
_DELTA_TONE = {"up": "positive", "down": "caution", "flat": "flat"}


def _slug_key(key_text: str) -> str:
    """Derive a stable JSON key from a driver-key label.

    e.g. "SHCOMP · 上证" → "shcomp", "CN 10Y · 国债" → "cn_10y".
    Uses the text left of the "·" separator, lowercased, non-alnum → "_".
    """
    left = key_text.split("·")[0].strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", left).strip("_")
    return slug or "driver"


def parse_html_brief(html: str) -> tuple[Optional[str], list[dict]]:
    """Parse the d13 HTML artifact (which we designed and know exactly).

    Returns (verdict, drivers). ``drivers`` mirrors the seats present in the
    card, in document order. Falls back to the generic placeholder set only
    if no driver blocks are found.
    """
    verdict = None
    m = re.search(
        r'<p\s+class="verdict-text">\s*(.+?)\s*</p>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        # Strip inner <span> wrappers — leave just the prose.
        verdict = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        verdict = re.sub(r"\s+", " ", verdict)

    drivers: list[dict] = []
    for key_text, value_html in _HTML_DRIVER_REGEX.findall(html):
        label = re.sub(r"\s+", " ", key_text.strip())
        # The value's first text node (before any span) is the number/token;
        # delta/unit spans are siblings we strip off.
        raw_value = re.split(r"<", value_html, maxsplit=1)[0].strip()
        raw_value = re.sub(r"\s+", " ", raw_value) or "--"
        # Tone: prefer the explicit delta class the card already carries.
        delta_m = re.search(r'class="delta\s+(up|down|flat)"', value_html, re.IGNORECASE)
        tone = _DELTA_TONE.get(delta_m.group(1).lower(), "neutral") if delta_m else "neutral"
        drivers.append(
            {
                "key": _slug_key(label),
                "label": label,
                "value": raw_value,
                "tone": tone,
            }
        )

    if not drivers:
        drivers = [
            {"key": k, "label": l, "value": "--", "tone": "muted"}
            for k, l in _DRIVER_ORDER
        ]
    return verdict, drivers


# Markdown fallback patterns — only used if HTML artifact missing.
_MD_PATTERNS = {
    "pmi_official": re.compile(r"官方(?:制造业)?\s*PMI[^\n]*?(?:至|为|到)?[^\n]*?(\d{2}\.\d{1})"),
    "pmi_private": re.compile(r"(?:RatingDog|私营|私人)\s*(?:制造业)?\s*PMI[^\n]*?(?:至|为)?[^\n]*?(\d{2}\.\d{1})"),
    "brent": re.compile(r"Brent\s*(?:油价|原油|油)[^\n]*?\$?\s*(\d{2,3})"),
    "us_jobs": re.compile(r"(\d{2}:\d{2}\s*ET)"),
}


def parse_markdown_brief(md: str) -> tuple[Optional[str], list[dict]]:
    verdict = None
    m = re.search(
        r"(?:一句话判断|今日市场[^\n]*?判断)\s*\n+([^\n#]+(?:\n(?!#{1,3}\s)[^\n#]+){0,3})",
        md,
    )
    if m:
        verdict = " ".join(line.strip() for line in m.group(1).splitlines() if line.strip())

    drivers_dict: dict[str, str] = {}
    for key, regex in _MD_PATTERNS.items():
        m = regex.search(md)
        drivers_dict[key] = m.group(1) if m else "--"

    drivers = [
        {
            "key": key,
            "label": label,
            "value": drivers_dict.get(key, "--"),
            "tone": _tone_for(key, drivers_dict.get(key, "--")),
        }
        for key, label in _DRIVER_ORDER
    ]
    return verdict, drivers


# ── Build payload ─────────────────────────────────────────────────────────
def build_payload(source: Optional[Path]) -> dict:
    now = datetime.now(timezone.utc).astimezone()
    if source is None:
        return {
            "verdict": None,
            "generated_at": None,
            "drivers": [
                {"key": k, "label": l, "value": "--", "tone": "muted"}
                for k, l in _DRIVER_ORDER
            ],
            "brief_md_path": None,
            "brief_html_path": None,
            "status": "empty",
            "fetched_at": now.isoformat(timespec="seconds"),
            "source_mtime": None,
        }

    text = source.read_text(encoding="utf-8")
    mtime = datetime.fromtimestamp(source.stat().st_mtime, tz=timezone.utc).astimezone()
    age_hours = (now - mtime).total_seconds() / 3600.0
    status = "fresh" if age_hours < FRESH_WINDOW_HOURS else "stale"

    if source.suffix.lower() == ".html":
        verdict, drivers = parse_html_brief(text)
    else:
        verdict, drivers = parse_markdown_brief(text)

    return {
        "verdict": verdict,
        "generated_at": mtime.isoformat(timespec="seconds"),
        "drivers": drivers,
        "brief_md_path": str(source) if source.suffix.lower() != ".html" else None,
        "brief_html_path": None,  # filled by emit_payload()
        "status": status,
        "fetched_at": now.isoformat(timespec="seconds"),
        "source_mtime": mtime.isoformat(timespec="seconds"),
        "age_hours": round(age_hours, 1),
    }


def _tone_for(key: str, value: str) -> str:
    if value in {"--", ""}:
        return "muted"
    if key in {"pmi_official", "pmi_private"}:
        try:
            v = float(value)
            return "positive" if v >= 50.5 else ("flat" if v >= 50.0 else "caution")
        except ValueError:
            return "flat"
    if key == "brent":
        return "neutral"
    return "accent"


# ── Emit ─────────────────────────────────────────────────────────────────
def emit_payload(payload: dict, copy_html: bool) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if copy_html and HTML_SOURCE.is_file():
        OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HTML_SOURCE, OUTPUT_HTML)
        payload["brief_html_path"] = str(OUTPUT_HTML)
    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── Entry ────────────────────────────────────────────────────────────────
def main() -> int:
    latest = find_latest_brief()
    payload = build_payload(latest)
    emit_payload(payload, copy_html=(latest is not None))

    # Status -> exit code per contract.
    status_to_code = {"fresh": 0, "stale": 1, "empty": 2}
    code = status_to_code.get(payload["status"], 2)

    # Compact stdout for the caller (Codex automation / cron).
    print(
        f"[brief-payload-builder] status={payload['status']} "
        f"source={latest or '<none>'} "
        f"-> {OUTPUT_JSON}"
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
