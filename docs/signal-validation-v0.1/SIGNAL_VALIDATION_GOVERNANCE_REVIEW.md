# Signal Validation Governance Review

Reviewer role: Evidence Auditor / Claim Boundary Reviewer (read-only)
Date: 2026-07-24
Window: Evidence Validation Review Window v0.1 — independent of the CLOSED Golden Pit window.

Scope of this review: verify that the produced evidence is real, that the
signal-to-outcome chain is intact, and that the final statement does not
exceed the evidence. This window did not run experiments, change code,
adjust strategy, add data, or reopen Golden Pit. No profitability, win rate,
or strategy value was assessed.

## Verification Performed

Read-only checks against raw artifacts (not just the summary documents):

- `evidence/auction_signal_snapshot_20260724_095651.json` SHA-256 recomputed = `4532569999bdd12e9863c1c835893b982f3c2ce95d69ebd9d6520d236263eac0` — matches the declared hash.
- `evidence/market_context_crosscheck_20260724_095631.json` SHA-256 recomputed = `72a17651b6a8885a228c64181ecb9c72e9bab0abc40c4edf01a49e7df1bfbff4` — matches the declared hash.
- `previous_zt` row count = 116; deterministic sample (sort by six-digit code ascending, first three) = `000011 / 000017 / 000035` — matches the report. Sampled values (+9.9867% / +4.9296% / -1.2422%) match the raw rows.
- Complete-set stats recomputed from raw JSON: 55 positive / 0 flat / 61 negative, median -0.1620%, mean +1.3633%, min -7.8227%, max +19.9959% — all match.
- Cross-check JSON confirms production endpoint returned `_qc.status=partial`, `source_type=real`, with `previous_zt` in `blocked_fields` — matches the report's stated provenance boundary.
- Market Outcome source artifacts exist: morning `loop_state.json` generated `2026-07-23T09:06:29+08:00`, close handoff generated `2026-07-23T16:13:11+08:00` (morning precedes close). All four drivers and the CONFIRMED×3 / DEVIATED×1 comparisons match the source files verbatim; close QC = `partial`.

## Evidence Reality

`VERIFIED`

Both raw captures exist, hash-match their declarations, and are traceable to a
named real provider (Eastmoney via AkShare) plus a production cross-check
(`touziagent.com/api/intel/market-context`). No mock, fixture, or fallback data
was used as row-level evidence. Signal objects carry provider-field timestamps;
outcome objects carry observation timestamps and sources. Negative cases are
present in both reports. Declared gaps are recorded rather than hidden.

## Data Provenance

`PARTIAL`

- Market Outcome side: `PASS`-grade. Morning artifact provably predates the
  close artifact; the observation-to-outcome ordering is immutable for the
  fixed 2026-07-23 set.
- Auction side: `PARTIAL`, correctly. The provider response carries no explicit
  effective-date field or retrieval identifier; `signal_date=2026-07-23` is
  inferred from `previous_zt` semantics at the T+1 retrieval time, and the row
  set was queried retrospectively on T+1. There is no immutable T-1 capture
  proving what the system knew before the outcome. The report holds this at
  PARTIAL for exactly this reason, which is the honest verdict.

Overall provenance is capped at `PARTIAL` by the auction temporal weakness. This
is disclosed, not concealed.

## Selection Bias

`PASS`

- Auction sampling is deterministic (sort by code, retain first three) and is
  accompanied by a full 116-row complete-set check, so favorable rows cannot be
  hidden. One MISS (`000035`, -1.24%) is retained in the three-row sample; the
  complete set shows a negative median.
- Market Outcome uses every driver in the fixed morning artifact, mapped by a
  fixed rule (CONFIRMED→HIT, DEVIATED→MISS, INCONCLUSIVE→NOT EVALUATED). No row
  was discarded or reinterpreted; the one MISS (创业板指) is retained and drives
  a recorded calibration note.
- No winner was selected after seeing outcomes. No signal reason was rewritten
  post-hoc; auction reasons come from provider fields, not narrative.

## Claim Boundary

`PASS`

The final status explicitly enumerates forbidden claims (auction effective /
profitable, 75% hit rate, investment advice, production readiness, Golden Pit
validated) and confines the allowed claim to observation recording plus
calibration against real outcomes. `Strategy Effectiveness: NOT CLAIMED` and
`Final Claim: NOT MADE` are stated in all three documents. Both reports repeat
that counts are bookkeeping, not hit rates, and that no order/fill/cost/return
series exists. No statement crosses from "observed" into "predictive" or
"effective".

## Trust Gate Alignment

Consistent. Where evidence is complete (fixed close artifact), the report allows
an observation-and-calibration claim. Where evidence is incomplete (auction
temporal provenance), the claim is lowered to PARTIAL and no strategy claim is
made. The reports do not upgrade "observation is available" into "prediction is
effective". This matches the Vera Trust Gate principle.

## Notes (disclosed, non-blocking)

- Auction HIT/MISS uses T+1 change at the 09:56 retrieval timestamp (intraday),
  not a T+1 close. The report states this and labels the field descriptive only.
- Brent and US 10Y are already-observed anchors rather than clean thresholded
  forecasts; the report flags them as weak calibration objects and marks them
  `HIT (limited)`. This self-qualification is appropriate.

These are already surfaced in the source reports and do not require a finding.

## Final Recommendation

`READY FOR DEMO` — as an evidence-governance / Trust Gate case only.

What is demonstrable and honest: the system can record a real market
observation, connect it to a later real market outcome (including misses), and
retain evidence boundaries and calibration notes. That is the allowed claim and
it is fully backed by verified artifacts.

What must NOT be demoed from these artifacts: any predictive edge, hit rate,
profitability, executable strategy, or production readiness. The auction chain
remains PARTIAL on temporal provenance and carries no execution evidence.

The valid position: the system honestly connects observation, evidence, and
outcome, and correctly refuses to claim more than the evidence supports.
