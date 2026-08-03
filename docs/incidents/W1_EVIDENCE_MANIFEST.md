# W1 Probe — Evidence Manifest (2026-08-02)

**Status:** PENDING RE-REVIEW  
**Builder:** CC (Claude Code)  
**Reviewer:** Codex (trust-reviewer skill)  
**Final closure:** WAIT — must be completed by independent process tomorrow

## Preserved Artifacts

| File | SHA-256 | Role |
|---|---|---|
| `w1_forward_probe.sh` (v1) | `436dbd64638cabc2d10b46201140bb8f3882d68a7025e0bd021dd702ce79e474` | Initial submission for review |
| `w1_forward_probe.sh` (v2) | `6af0b0b6db1f91e147a6a4437b540f11a1378fdc4e696f1bf6eaaf5ce16e89c0` | Post-review fixes applied |
| `W2_GATE_SEMANTIC_VERIFICATION.md` | (no hash) | H4 disproven — gate semantics clarified |
| `W1_FORWARD_OBSERVATION_DECISION_MATRIX.md` | (no hash) | Predefined criteria for tomorrow's run |
| `AUCTION_HISTORICAL_PRODUCTION_SUCCESS_VERIFICATION.md` | (no hash) | P0 closed — NOT FOUND |

## Codex Review Findings (Initial)

1. **P1 — Evidence overwrite risk** → BLOCKED → Fixed: unique run isolation (PID + datetime in OUTDIR)
2. **P1 — Temporal provenance gap** → BLOCKED → Fixed: record TS_START and TS_END, log both
3. **P2 — Timezone not enforced** → BLOCKED → Fixed: `export TZ=Asia/Shanghai`
4. **P2 — 30s interval drifts** → PARTIAL → Accepted with documentation
5. **P2 — Field extraction heuristic** → BLOCKED → Fixed: removed `[0:2]` truncation, flatten full tree

## Re-review

**Not yet completed.** One attempt (2026-08-03 00:31) produced unrelated output — Codex read
nginx server blocks instead of the probe script. Session drift confirmed.

Must be performed by Codex independently tomorrow morning.
Do NOT accept builder's self-assessment. Verdict delta must come from reviewer.

## launchd Job

```
Label:  com.zhuanz.w1-auction-forward-probe
Fires:  2026-08-03 (Mon) 09:24 Asia/Shanghai
Script: /Users/Zhuanz/finance-suite/docs/incidents/w1_forward_probe.sh
Status: loaded (exit 0)
```

## Tomorrow's Sequence

1. **Re-review** — Codex independently reviews v2 script
2. If PARTIAL or above → let W1 run at 09:24, apply Decision Matrix after
3. If still BLOCKED → manual curl at 09:28, do not execute probe script
4. Builder does NOT announce the verdict — reviewer does
