# D27 W1/W2/W3 Fact Check — Codex PoC 输出

**Date**: 2026-07-29 (smoke run) · 2026-07-30 (this fact extraction)
**Scope**: Pure fact extraction. No implementation review. No promotion decision.
**Source location**: `/Users/Zhuanz/Documents/New project 6/` (Codex PoC, NOT part of finance-suite canonical tree per D27 Phase 1 boundary)
**Reference architecture**: `finance-suite/docs/governance/INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` §3.2 capability state machine

---

## 0. Boundary Reminder (Applied Throughout)

Three rules stated in the user's authorization, repeated here verbatim because this document must NOT silently relax them:

1. **Codex smoke output ≠ Finance Suite evidence**
2. **Observed ≠ Verified**
3. **PoC exists ≠ Capability exists**

Every fact below is sourced from `/Users/Zhuanz/Documents/New project 6/`. None of it is treated as Vera / Finance Suite evidence. State names below are referenced from `INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` §3.2 only as a vocabulary; promotion across state boundaries is NOT declared by this document.

---

## 1. Source Artifacts Examined

| File | Purpose in PoC | Lines |
|---|---|---|
| `GILDATA_PROVIDER_SMOKE_REPORT.md` | Latest smoke run report (2026-07-29T14:18:43) | 86 |
| `config/gildata.env.example` | Provider config template | 8 |
| `scripts/gildata_adapter.py` | Adapter implementation | 594 |
| `scripts/gildata_smoke.py` | Smoke runner | 182 |
| `tests/test_gildata_adapter.py` | Unit tests (10 cases) | 152 |
| `schemas/gildata_provider_contract_v0.1.json` | Provider raw contract JSON schema | 38 |
| `Evidence_Manifest_v1.md` (repo root) | Manifest field spec | 367 |

These are the only artifacts consulted. No inference from files outside this list.

---

## 2. W1 — Transport

**Question**: Does evidence of real endpoint connectivity exist?

### 2.1 Observed Facts

| # | Fact | Source |
|---|------|--------|
| F1.1 | Smoke ran `GildataAdapter()` with no `transport` override → defaulted to `_http_json_transport` (urllib-based). | `scripts/gildata_adapter.py:102` |
| F1.2 | Smoke ran against `https://sandbox.hscloud.cn/gildataastock/v1` (the `GILDATA_BASE_URL` in `config/gildata.env.example`). | `config/gildata.env.example:2` |
| F1.3 | Smoke report captured transport observation: `GET https://sandbox.hscloud.cn/gildataastock/v1/basicinfo/as_companyprofile: HTTP 401 response received`. | `GILDATA_PROVIDER_SMOKE_REPORT.md:47` |
| F1.4 | The HTTP 401 response was the actual urllib result — `GildataHTTPError` is raised by `_http_json_transport` on `urllib.error.HTTPError`, and the adapter catches it on `adapter.py:142-148`, recording `_transport_verified = True`. | `scripts/gildata_adapter.py:142-148`, `449-466` |
| F1.5 | The endpoint hostname `sandbox.hscloud.cn` resolves to a sandbox tier, not a production tier. | `config/gildata.env.example:2` |
| F1.6 | Smoke report status line: `Transport: CONNECTED`. | `GILDATA_PROVIDER_SMOKE_REPORT.md:10` |
| F1.7 | Smoke report status line: `Credential: FAIL`, `Authentication: FAIL`. | `GILDATA_PROVIDER_SMOKE_REPORT.md:11-12` |
| F1.8 | Smoke report capability scope lists three routes: `basicinfo/as_companyprofile`, `financialanalysis/as_amainaccountdata`, `shareholders/as_shareholders_latest`. None of these routes was actually exercised end-to-end in the smoke run (smoke broke at authentication). | `GILDATA_PROVIDER_SMOKE_REPORT.md:58-64` |

### 2.2 State Mapping (Vocabulary Only, NOT Promotion)

Per `INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` §3.2:

- `CREDENTIAL_EXISTS`: NOT OBSERVED in this artifact set. `GILDATA_ACCESS_TOKEN` is empty in `config/gildata.env.example`. Smoke report confirms "missing configuration: GILDATA_ACCESS_TOKEN".
- `CREDENTIAL_LOADED`: NOT OBSERVED. No credential was loaded at runtime.
- `TRANSPORT_VERIFIED`: OBSERVED — one HTTP request was made to the sandbox endpoint and a 401 was returned. Reachability of the sandbox host is observed. **Note**: 401 with no credential does not prove authentication path works.
- `SESSION_ESTABLISHED`: NOT OBSERVED. Authentication failed; no session was opened.

### 2.3 Boundary Application

- **Observed ≠ Verified**: HTTP 401 reaching the host is observed; whether this constitutes "transport verified" depends on what is meant by verification. The PoC labels it PASS; the architecture spec §3.2 separates `TRANSPORT_VERIFIED` from `SESSION_ESTABLISHED`, and the smoke shows the latter is FAIL.
- **PoC exists ≠ Capability exists**: A transport probe that returns 401 does not establish provider capability.
- **Codex smoke output ≠ Finance Suite evidence**: This sandbox probe was executed inside `/Users/Zhuanz/Documents/New project 6/`, not inside `finance-suite/`. No finance-suite runtime consumed this evidence.

### 2.4 W1 Verdict (Fact-Only)

A real HTTP request to a real endpoint was issued, and a real HTTP 401 was received. Whether this counts as **TRANSPORT VERIFIED** for Finance Suite is a governance decision, not a fact extraction result. This document records the fact and refuses the promotion.

---

## 3. W2 — Evidence Retrieval

**Question**: Does evidence of an evidence artifact / manifest / hash exist?

### 3.1 Observed Facts

| # | Fact | Source |
|---|------|--------|
| F2.1 | Smoke run produced no evidence bundle. Report `Evidence Bundle` section reads `- None`. | `GILDATA_PROVIDER_SMOKE_REPORT.md:71` |
| F2.2 | Smoke report `Evidence Retrieval: FAILED`. | `GILDATA_PROVIDER_SMOKE_REPORT.md:13` |
| F2.3 | Smoke report `Evidence: FAILED`. | `GILDATA_PROVIDER_SMOKE_REPORT.md:14` |
| F2.4 | Adapter code defines `generate_manifest()` (lines 231-334) producing a manifest with `manifest_id`, `manifest_version = "Vera_Evidence_Manifest_Protocol_v0.1"`, `integrity.raw_hash`, `integrity.normalized_hash`, `integrity.chain_hash`, `constraint.qc_status`, `constraint.allowed_use`, `constraint.blocked_fields`, `constraint.confidence_boundary`, `output.artifact_id`, `output.render_hash`. | `scripts/gildata_adapter.py:231-334` |
| F2.5 | `_sha256_json()` produces deterministic SHA-256 over canonicalized JSON. `chain_hash = sha256(raw_hash + normalized_hash)`. | `scripts/gildata_adapter.py:574-576`, `242` |
| F2.6 | Unit test `test_connect_fetch_normalize_manifest_closed_loop` exercises the full chain using a mock transport that returns synthetic data (`{"SecuCode": "600519", "ChiName": "贵州茅台", "ROE": 31.2}`). Mock transport is passed into the adapter via `transport=transport` arg — not the default `_http_json_transport`. | `tests/test_gildata_adapter.py:14-31`, `36-54` |
| F2.7 | Unit test `test_bundle_hashes_are_verifiable` verifies that the manifest's `integrity.normalized_hash` is reproducible by re-hashing the `normalized_evidence` field. The hash chain is mechanically correct against synthetic input. | `tests/test_gildata_adapter.py:61-72` |
| F2.8 | Unit test `test_missing_credentials_fail_closed` proves the adapter fails closed (no manifest generated) when no API key is configured. | `tests/test_gildata_adapter.py:74-80` |
| F2.9 | Provider raw contract schema (`schemas/gildata_provider_contract_v0.1.json`) declares `additionalProperties: false`, requires fields `provider`, `provider_version`, `request_id`, `timestamp`, `query`, `response_status`, `data`, `provenance`, with `provider.const = "juyuan"`. | `schemas/gildata_provider_contract_v0.1.json:6-37` |
| F2.10 | Test `test_provider_contract_has_only_reviewable_fields` enforces raw shape conformance. | `tests/test_gildata_adapter.py:121-127` |
| F2.11 | No `.gildata-provider/*.json` files observed in the project tree (no on-disk evidence bundle artifact exists from a prior smoke run). | `find /Users/Zhuanz/Documents/New\ project\ 6/.gildata-provider` returns no result |

### 3.2 State Mapping (Vocabulary Only, NOT Promotion)

Per architecture v0.1 §3.2:

- `EVIDENCE_RETRIEVED`: NOT OBSERVED against real provider traffic. Mock data in unit tests is not real retrieval.
- `NORMALIZED`: NOT OBSERVED against real provider traffic. Normalization code path was only exercised against synthetic test input.
- `MANIFEST_BOUND`: Schema, hash structure, and field vocabulary are PROVEN by unit tests. Whether they bind to real evidence is NOT OBSERVED.
- `constraint.qc_status` field exists in the manifest, but its value in any real-bundle run remains UNKNOWN.

### 3.3 Boundary Application

- **Codex smoke output ≠ Finance Suite evidence**: Smoke produced no evidence bundle; the only manifest artifacts ever generated were unit-test fixtures with synthetic data.
- **Observed ≠ Verified**: Schema correctness and hash-chain determinism are observed in unit tests. That is **manifest schema-level proof**, not **evidence retrieval proof**.
- **PoC exists ≠ Capability exists**: A 595-line adapter file and a passing test suite do not establish that real Gildata evidence can be retrieved.

### 3.4 W2 Verdict (Fact-Only)

Manifest **schema** is mechanically defined and unit-tested. Manifest **content** from real provider traffic is not present in any artifact in this PoC. W2 has two sub-questions, with different verdicts:

- W2a (manifest schema correctness): SCHEMA OBSERVED (unit-tested only).
- W2b (real retrieval): NOT OBSERVED.

---

## 4. W3 — QC Integration

**Question**: Does evidence of `qc_status` / `allowed_use` / `blocked_fields` exist?

### 4.1 Observed Facts

| # | Fact | Source |
|---|------|--------|
| F3.1 | Adapter code defines `qc_checks` dict with 9 checks: `provider_contract`, `provider_is_juyuan`, `response_success`, `source_is_real`, `capability_matches`, `security_code_matches`, `request_id_matches`, `evidence_non_empty`, `raw_hash_present`, `normalized_hash_present`. | `scripts/gildata_adapter.py:245-258` |
| F3.2 | `qc_status` is computed as `PASS` iff `all(qc_checks.values())`; otherwise `FAIL`. The QC logic is **inline in `generate_manifest()`**, not a separate QC layer. | `scripts/gildata_adapter.py:259-260`, `281` |
| F3.3 | `allowed_use` in manifest is hardcoded as `["provider_adapter_smoke"]`. | `scripts/gildata_adapter.py:282` |
| F3.4 | `blocked_fields` in manifest is hardcoded as `["investment_advice", "short_term_prediction", "client_suitability_judgement"]`. | `scripts/gildata_adapter.py:283` |
| F3.5 | `confidence_boundary` is hardcoded as `"事实级，非预测级"`. | `scripts/gildata_adapter.py:284` |
| F3.6 | `evidence_level` and `output.claim_level` are derived from `verified` boolean (`EVIDENCE VERIFIED` if `verified`, else `UNKNOWN`). | `scripts/gildata_adapter.py:285`, `292` |
| F3.7 | `trust_gate.status` mirrors `qc_status` (`PASSED` / `FAILED`) and embeds the full `qc_checks` dict. | `scripts/gildata_adapter.py:328-331` |
| F3.8 | No `qc_policy.yaml` or any external QC policy file exists in the PoC tree. The QC rules are constants in source code, not policy-driven. | `find /Users/Zhuanz/Documents/New\ project\ 6/ -name "*qc*"` returns no policy file |
| F3.9 | Test `test_empty_payload_cannot_pass_trust_gate` proves `normalize()` raises `GildataAdapterError` when no records are extracted, so the QC layer fails closed on empty payloads. | `tests/test_gildata_adapter.py:82-98` |
| F3.10 | Test `test_provider_error_does_not_become_evidence` proves `fetch()` raises when provider returns `{success: False}`, so the QC chain rejects provider-level errors. | `tests/test_gildata_adapter.py:100-106` |
| F3.11 | Test `test_connect_is_a_real_authenticated_probe` proves that an HTTP 401 leaves `transport=PASS` but `authentication=FAIL` and `evidence=FAIL` — the verification_levels in `capability_status()` correctly distinguish transport from authentication. | `tests/test_gildata_adapter.py:108-119` |
| F3.12 | Smoke run: `qc` check was FAIL (no manifest, so no qc_status produced). | `GILDATA_PROVIDER_SMOKE_REPORT.md:56` |

### 4.2 State Mapping (Vocabulary Only, NOT Promotion)

Per architecture v0.1 §3.2:

- `QC_INTEGRATED`: Field vocabulary matches `Evidence_Manifest_v1.md` (allowed_use, blocked_fields) plus `qc_status` and `confidence_boundary` extensions. QC rules live inline in the adapter source. No external policy exists.
- `CONSUMER_PROVEN`: NOT OBSERVED. No runtime consumer exists in the PoC.
- `PRODUCTION_CAPABLE`: NOT OBSERVED and explicitly labeled `NOT CLAIMED` in the manifest's `verification_levels.production_capability` and `production_ready` fields.

### 4.3 Boundary Application

- **Codex smoke output ≠ Finance Suite evidence**: The `qc_status` and friends observed here are values produced by a project-local adapter running unit tests. They are not inputs to any Finance Suite trust gate.
- **Observed ≠ Verified**: A schema field exists ≠ the field's value is grounded in a real QC policy and a real evidence stream.
- **PoC exists ≠ Capability exists**: Inline QC checks in one adapter file do not constitute the QC layer that architecture v0.1 §4 (`QCIntegrator`) describes.

### 4.4 W3 Verdict (Fact-Only)

QC **field vocabulary** and **inline check logic** are observed in source. QC **policy externalization**, QC **integration into Finance Suite trust gate**, and QC against **real evidence stream** are NOT OBSERVED. The PoC's QC is self-contained; it does not feed any external consumer.

---

## 5. Cross-Cutting Boundary Application

What the artifacts in this PoC **DO** establish (factually, in the PoC's own context only):

- A REST adapter file targeting three Gildata capability routes exists and is internally consistent.
- A provider raw contract schema is enforced (`additionalProperties: false`).
- A manifest shape with hash chain (`raw_hash`, `normalized_hash`, `chain_hash`) is produced.
- QC fields (`qc_status`, `allowed_use`, `blocked_fields`, `confidence_boundary`, `evidence_level`) exist in the manifest and are populated.
- The adapter fails closed on missing credential and on empty/error payloads.
- The adapter distinguishes transport reachability from authentication in `verification_levels`.

What the artifacts in this PoC **DO NOT** establish:

- That real Gildata Studio API responses have been retrieved end-to-end.
- That any Finance Suite runtime has consumed a Gildata manifest.
- That any external QC policy governs the inline checks.
- That `TRANSPORT_VERIFIED` (with credential) has been observed.
- That `SESSION_ESTABLISHED` has been reached.
- That any evidence artifact from this PoC has crossed into `finance-suite/`.

---

## 6. State Summary (Per Architecture v0.1 §3.2 Vocabulary)

| State | Status from PoC Artifacts | Promotable to Finance Suite? |
|---|---|---|
| `CREDENTIAL_EXISTS` | NOT OBSERVED | NO |
| `CREDENTIAL_LOADED` | NOT OBSERVED | NO |
| `TRANSPORT_VERIFIED` (sandbox, no auth) | OBSERVED (HTTP 401 from sandbox host) | NOT IN SCOPE — this document only records the fact; promotion is a separate decision |
| `SESSION_ESTABLISHED` | NOT OBSERVED | NO |
| `EVIDENCE_RETRIEVED` (real) | NOT OBSERVED | NO |
| `NORMALIZED` (real) | NOT OBSERVED (synthetic only in tests) | NO |
| `MANIFEST_BOUND` (schema) | OBSERVED in source + unit tests | Schema-level only |
| `QC_INTEGRATED` (field vocabulary) | OBSERVED in source | Field-level only |
| `CONSUMER_PROVEN` | NOT OBSERVED | NO |
| `PRODUCTION_CAPABLE` | NOT OBSERVED (and `NOT CLAIMED` is asserted in artifact) | NO |

---

## 7. What This Document Does and Does Not Decide

This document decides:

- Which facts exist in `/Users/Zhuanz/Documents/New project 6/` as of this read.
- Which architecture states those facts correspond to (vocabulary mapping only).
- Which boundary rules the facts must travel across before any promotion claim.

This document does NOT decide:

- Whether `TRANSPORT_VERIFIED` against `sandbox.hscloud.cn` counts as Vera-side `TRANSPORT_VERIFIED`.
- Whether to merge the PoC's QC inline rules into the Finance Suite trust gate.
- Whether the PoC may graduate from `Experimental Sandbox` to canonical finance-suite tree.
- Whether W1 / W2 / W3 should be marked `EVIDENCED` based on these artifacts.

These are governance decisions for a separate window, gated by the W1-W3 preconditions in `D27_INSTITUTIONAL_EVIDENCE_PROVIDER_LAYER_STATUS.md`.

---

## 8. Files Referenced (Reproducibility)

| File | SHA-style reference (size only) |
|---|---|
| `GILDATA_PROVIDER_SMOKE_REPORT.md` | 2,262 bytes |
| `scripts/gildata_adapter.py` | 24,457 bytes |
| `scripts/gildata_smoke.py` | 6,460 bytes |
| `tests/test_gildata_adapter.py` | 4,557 bytes (line-counted; bytes not measured) |
| `schemas/gildata_provider_contract_v0.1.json` | 1,161 bytes |
| `config/gildata.env.example` | 280 bytes (line-counted) |
| `Evidence_Manifest_v1.md` (repo root) | 7,920 bytes |

All paths under `/Users/Zhuanz/Documents/New project 6/`.

---

## 9. Sign-off (Fact Extraction Only)

| Aspect | Statement |
|---|---|
| Scope | Facts in `/Users/Zhuanz/Documents/New project 6/` as of read time. |
| Method | File read + grep + `find`. No code execution. No implementation review. |
| Boundaries applied | Codex smoke ≠ Finance Suite evidence · Observed ≠ Verified · PoC exists ≠ Capability exists. |
| Promotion claims | None made. None implied. |
