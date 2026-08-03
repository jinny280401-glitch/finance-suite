# Presentation Truth Guard Blocking RCA

Date: 2026-07-27 (Asia/Shanghai)

Classification: Capability Claim Governance Finding

Canonical finding: **A capability claim exceeded its evidence maturity level.**

Framework: `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md`

Evidence protocol: `docs/evidence/Vera_Evidence_Manifest_Protocol_v0.1.md`

Originating scope: `/api/analyze`, authenticated three-case evidence, Presentation shell/live-proof boundary.

Governance constraints: no Truth Guard rule change, no fabricated evidence, no shell-to-live promotion, no Production Ready claim.

## Issue

`stock.html` and `deep-research.html` unconditionally display:

```text
Presentation Truth Guard
/api/analyze authenticated 3-case evidence is blocked.
Current page is a presentation shell, not verified live proof.
Live Presentation: NOT ESTABLISHED
Reality -> Presentation: HOLD / FAIL
Production Ready: NOT CLAIMED
```

The message is accurate for the currently provable evidence boundary, but it is a static page declaration rather than the output of a runtime gate evaluation.

## Root Cause

The blocking condition is an evidence-chain discontinuity, not a proven `/api/analyze` outage:

1. The public route is alive and authentication is enforced, but an authenticated current run was not available during this audit.
2. The repository contains three-case rendered UI evidence, but its own raw-API table marks every required response field `UNKNOWN` because same-session raw bodies were not captured.
3. No durable raw response artifacts, request correlation IDs, response hashes, or authenticated replay receipt were found that bind all three requests to their rendered outputs.
4. The page is therefore provable as a deployed Presentation shell, but not as current live proof of `Reality -> Presentation` for three authenticated cases.
5. The Truth Guard notice is hard-coded and unconditional. It does not inspect current auth, evidence manifests, or runtime results. Shell state and live-proof state are represented in the same page, but only the shell state is established.

## Evidence

### Current live checks

Observed on 2026-07-27:

| Check | Result | Meaning |
|---|---|---|
| `GET /api/health` | HTTP 200, `{"status":"ok"}` | Service transport is alive only. |
| `GET /api/check-auth` without session | HTTP 401 | Auth boundary is active. |
| `POST /api/analyze` without session | HTTP 401 | Route exists and fails closed when unauthenticated; business/runtime success is not tested. |
| `GET /app/stock.html` | HTTP 200 | Live shell exists. |
| Live `stock.html` SHA-256 | `0c13e6f2f7e7d67687835cc0d8a2be14404a95ea730311a783589daa10914d7a` | Exact match with local `app/stock.html`. |
| `GET /app/deep-research.html` | HTTP 200 | Live shell exists. |
| Live `deep-research.html` SHA-256 | `a2624808c33d669e037d07702872802ba857d0fb11da26bfa13d5b5dbb7a8652` | Does not match the newer local source. |

HTTP 200 and shell deployment do not establish authenticated business success.

### Three-case evidence source

The discoverable source is `docs/three_case_evidence_pack_20260629_v1.md`, covering `600519.SH`, `600036.SH`, and `600710.SH` from a logged-in Chrome session. It records rendered reports, trust panels, eight availability items, and no visible missing-token leak.

However, for all three cases it explicitly records the following as `UNKNOWN`: HTTP status, `success`, `cached`, result length, `_qc.status`, top-level and `_qc` `data_availability`, and top-level and `_qc` `section_data_usage`. It also says raw API bodies were not captured.

Later status summaries claim Raw Trust Data was proven, but the underlying raw three-case artifacts were not found in this repository. A summary claim cannot replace the missing primary evidence.

### Presentation trigger

The notice is literal HTML in:

- `app/stock.html:670-674`
- `app/deep-research.html:406-410`

There is no conditional trigger, evidence lookup, auth check, or signed runtime status behind the notice. The page can call `/api/analyze` and can render Trust Presentation fields after a successful response, but those capabilities do not make the page itself live proof.

## Current State

| Capability boundary | State |
|---|---|
| Public service transport | AVAILABLE (`/api/health` 200) |
| `/api/analyze` route | PRESENT / AUTH-PROTECTED |
| Current authenticated `/api/analyze` business result | NOT VERIFIED IN THIS AUDIT |
| Historical three-case rendered evidence | EXISTS, RENDERED-ONLY / WITH FINDINGS |
| Historical three-case raw evidence | NOT DURABLY AVAILABLE / NOT INDEPENDENTLY VERIFIABLE |
| Presentation shell | LIVE for `stock.html`; LIVE but source-drifted for `deep-research.html` |
| Live Presentation proof | NOT ESTABLISHED |
| Reality -> Presentation | HOLD / FAIL |
| Production Ready | NOT CLAIMED |

This is not merely a decorative demo page: it contains a real authenticated API client and renderer. But under the current evidence boundary it must be treated as a presentation shell, not verified live proof.

## Expected State

The page may declare `Live Presentation` only when a fresh, authenticated, reproducible evidence bundle proves all of the following for three governed cases:

1. Request identity: case ID, request timestamp, environment, authenticated principal class (redacted), and correlation ID.
2. Raw response: HTTP status, business `success`, cache state, result presence, `_qc.status`, `data_availability`, and `section_data_usage`.
3. Integrity: SHA-256 for each redacted raw response and rendered HTML artifact.
4. Mapping: correlation between each raw response and its rendered DOM artifact.
5. Presentation checks: trust notice, availability summary, partial/missing disclosure, section usage, and no raw `nan/null/None/N/A` leak.
6. Recency and authority: evidence TTL, verifier identity, source commit/deploy checksum, and explicit gate verdict.
7. Negative checks: unauthenticated 401 and failed/partial responses remain controlled and cannot be promoted.

Only the scoped `Reality -> Presentation` status may then be promoted. `Production Ready` remains a separate gate.

## Recommended Fix

### 1. Repair evidence collection, not the guard

Run a new authenticated three-case verification through an approved test account and browser automation. Capture redacted network response bodies from the same session, server/request correlation IDs, rendered DOM snapshots, timestamps, hashes, and the deployed page checksum. Do not extract or persist cookies, passwords, or tokens.

### 2. Create a durable evidence manifest

Store one manifest per run with explicit `PASS`, `PARTIAL`, `FAIL`, or `UNKNOWN` fields. The verdict must fail closed if any case lacks raw response, render mapping, freshness, or integrity evidence. Archive the primary artifacts beside the manifest; do not rely on prose-only status summaries.

### 3. Separate shell status from proof status

Keep the current Truth Guard until the new evidence package passes review. In a separately authorized implementation window, let the UI consume a read-only, server-generated presentation-status document that references the reviewed manifest and expires automatically. Missing, expired, mismatched, or unsigned status must remain `NOT ESTABLISHED`.

This changes how evidence is surfaced, not the Truth Guard decision rule.

### 4. Reconcile source/deploy identity

Resolve the `deep-research.html` local/live checksum drift before using it in evidence. Record the canonical source commit, deployed file hash, target path, and rollback artifact. Do not infer live behavior from a newer local file.

### 5. Legal competition Demo mode

If the competition only needs a reliable demonstration, use a separate explicit route such as `/demo/analysis` or a static roadshow artifact with these controls:

- Always show `DEMO MODE - TEST/RECORDED DATA - NOT LIVE`.
- Use versioned, immutable, pre-reviewed fixtures or recordings with source and capture time.
- Do not call or imitate production `/api/analyze` success.
- Disable or relabel actions that imply live execution.
- Keep demo evidence namespace and analytics separate from production evidence.
- State `Presentation Demo: ESTABLISHED` only; keep `Live Presentation: NOT ESTABLISHED` and `Production Ready: NOT CLAIMED`.

## Final Verdict

The Truth Guard is not malfunctioning. It is correctly preserving the boundary created by missing durable authenticated raw evidence and source/deploy drift. The compliant repair is to restore a reproducible evidence chain and separately attest its freshness, not to hide the banner or promote the shell.

This RCA is therefore archived as the first canonical Capability Claim Governance finding, not merely as an `/api/analyze` incident report.
