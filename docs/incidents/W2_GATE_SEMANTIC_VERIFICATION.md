# W2: Auction Time Gate Semantic Verification

**Date:** 2026-08-02  
**Window:** W2 Gate Semantics (read-only)  
**Status:** CLOSED  
**Verdict:** H4 DISPROVEN for branch `scripts/auction_data.py`; INFERRED (not proven) for production `app/auction_data.py`

---

## Question

Does the time gate introduced on 2026-07-17 block the **09:25:00 - 09:30:00** window?

---

## Evidence Source

Git branch `codex/auction-time-gate-qc-20260717` (commit `9cdbadb`), file `scripts/auction_data.py`.

This is NOT the production Web API path. Production uses `app/auction_data.py` (15860 bytes, Jul 17 09:58), which was patched independently and is not on this branch. However, both files share identical grep signatures for the gate (`< 92500`, `< 93000`, `gate_reason="auction_not_complete_before_09_25"`), so the segmentation is **inferred** to be the same until proven otherwise by W1 or direct SSH read.

---

## market_phase() Implementation (lines 20-44, branch)

```python
def market_phase(at: datetime | None = None) -> str:
    """Return the A-share phase relevant to auction-result readiness."""
    now = at or datetime.now(_SHANGHAI_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_SHANGHAI_TZ)
    else:
        now = now.astimezone(_SHANGHAI_TZ)
    if now.weekday() >= 5:
        return "non_trading_day"

    hhmmss = now.hour * 10000 + now.minute * 100 + now.second

    if hhmmss < 91500:
        return "pre_open"
    elif hhmmss < 92500:                    # ← blocks up to 09:24:59
        return "auction_in_progress"
    elif hhmmss < 93000:                    # ← 09:25:00 - 09:29:59
        return "auction_complete"           # ← THIS is the pass-through phase
    elif hhmmss < 113000:
        return "morning_session"
    elif hhmmss < 130000:
        return "lunch_break"
    elif hhmmss < 150000:
        return "afternoon_session"
    elif hhmmss < 153000:
        return "closing_auction"
    else:
        return "post_market"
```

**Segmentation:**

| Time | hhmmss | Phase | Gate blocks? |
|------|--------|-------|--------------|
| 09:24:59 | 92459 | `auction_in_progress` | YES — `gate_reason="auction_not_complete_before_09_25"` |
| **09:25:00** | **92500** | **`auction_complete`** | **NO** |
| 09:29:59 | 92959 | `auction_complete` | NO |
| 09:30:00 | 93000 | `morning_session` | NO (gate only checks phase, not absolute time) |

---

## Test Assertions (tests/test_auction_time_gate_qc.py)

```python
def test_market_phase_boundary_at_0925():
    assert market_phase(datetime(2026, 7, 17, 9, 24, 59, tzinfo=SHANGHAI)) == "auction_in_progress"
    assert market_phase(datetime(2026, 7, 17, 9, 25, 0, tzinfo=SHANGHAI)) == "auction_complete"

def test_qc_allows_valid_post_auction_data():
    qc = mcp_server._qc_auction(_data("2026-07-17T09:25:05+08:00", True))
    assert qc["status"] == "success"
    assert qc["auction_results_ready"] is True
    assert qc["blocked_fields"] == []
```

**09:25:05** explicitly passes QC with `status=success` and zero blocked fields.

---

## Conclusion

**For branch `scripts/auction_data.py`:**

The gate was designed to block requests **before 09:25:00** (the 09:19 incident that triggered its creation). The 09:25:00-09:29:59 window is classified as `auction_complete` and is the **only** phase where auction conclusions are allowed.

**H4 (Time Gate blocks 09:25-09:30) is DISPROVEN** for the branch implementation.

**For production `app/auction_data.py`:**

Grep shows identical threshold literals and error strings. The segmentation is **inferred** to match the branch, but this is not byte-level proof. W1 will provide runtime confirmation:
- If production returns `gate_reason` during 09:25-09:30 → production diverged from branch
- If no `gate_reason` appears and content is present → production matches branch

---

## Boundaries

- This verification only reads local git history. No production access, no SSH, no code modification.
- W2 answers the gate semantics question. It does NOT answer whether production currently has capability inside that window — that is W1's scope.
- The original hypothesis ("trigger drifted from 09:25 to 09:30") remains at `STRONGLY SUPPORTED / NOT PROVEN`. W2 only rules out gate interference as the cause.

---

## Impact on RCA

```
H4 (Gate blocks 09:25-09:30):  DISPROVEN (branch) / INFERRED (production)
                                No longer a candidate root cause for the window
```

Remaining open items from the original RCA investigation notes:
- H1 (Trigger at 09:30) — observed current state, historical state UNKNOWN
- Historical Production Success — P0 closed as NOT FOUND
- W1 Forward Observation — scheduled for 2026-08-03 09:24

No changes to production, code, or configuration.
