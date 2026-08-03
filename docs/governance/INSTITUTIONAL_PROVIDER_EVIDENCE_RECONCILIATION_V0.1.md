# Institutional Provider Evidence Reconciliation v0.1

**Audit date:** 2026-07-31  
**Status:** COMPLETE  
**Mode:** READ-ONLY EVIDENCE AUDIT  
**Capability effect:** NONE

## 1. Purpose

This record reconciles existing Wind, Choice, and iFinD code entries with the evidence currently available in the repository. It does not connect a provider, validate a new credential, change an adapter, or promote any capability claim.

This document deliberately performs **Observation -> Existing Evidence consistency** only. It makes no integration or production commitment.

## 2. Evidence Semantics

- **FOUND:** an artifact or code entry is present; execution is not implied.
- **VERIFIED (scoped):** supported by a dated or otherwise bounded execution record.
- **HISTORICALLY VERIFIED (secondary record):** asserted by a later governance record, but the primary execution receipt is not present in the current worktree.
- **UNKNOWN / NOT PROVEN:** available evidence cannot establish the state.
- **NOT FOUND:** repository inspection found no artifact for the stated link; this is not proof that none exists outside the inspected repository.
- **NOT CLAIMED:** production or research capability must not be inferred.

## 3. Provider Matrix

| Provider | Code Entry | SDK | Credential | Session | Evidence / Manifest | Research Runtime Consumer | Reconciled Status |
|---|---|---|---|---|---|---|---|
| Wind | FOUND | Local SDK NOT FOUND; historical scoped check also unavailable | UNKNOWN | NOT PROVEN | NOT PROVEN | NOT FOUND; direct MCP entry is not a Research Runtime consumer | NOT CLAIMED |
| Choice | FOUND | EXISTS in local environment; server SDK historically observed | HISTORICALLY VERIFIED by secondary governance record; primary receipt NOT FOUND in current worktree | HISTORICALLY VERIFIED by secondary governance record; current session UNKNOWN | Real Evidence Manifest binding NOT PROVEN; fixture-based shadow evidence does not qualify | NOT FOUND beyond direct tool and shadow smoke | PARTIAL / NOT CLAIMED |
| iFinD | FOUND | Local SDK NOT FOUND; server SDK historically observed | UNKNOWN | Current session UNKNOWN | TO VERIFY; Evidence Manifest binding NOT FOUND | NOT FOUND beyond direct MCP tool | AVAILABLE (limited, historical boundary) / NOT CLAIMED |

## 4. Provider Evidence Cards

### 4.1 Wind

**Observed**

- `scripts/wind_data.py` and the `wind_query` MCP entry exist.
- The graph-visible callers of `wind_query` are tests; no provider-specific binding was found under `research_runtime/`.
- The scoped 2026-07-17 data-source check recorded WindPy unavailable, Wind terminal not running, and `wind:false`.
- A read-only local module lookup on 2026-07-31 returned `WindPy: NOT_FOUND`.

**Boundary**

Code Entry is **FOUND**. Credential, live Session, Evidence generation, Evidence Manifest binding, and Research Runtime consumption are **NOT PROVEN**. Wind capability remains **NOT CLAIMED**.

### 4.2 Choice

**Observed**

- `scripts/emquant_data.py` and the `emquant_query` MCP entry exist.
- `scripts/choice_provider.py` normalizes supplied table data; it does not itself establish a live Choice session.
- `scripts/smoke_choice_provider_shadow.py` uses fixtures. Mock/shadow success is not real provider evidence.
- A read-only local module lookup on 2026-07-31 returned `EmQuantAPI: EXISTS`.
- The effective Capability Claim Matrix records Credential acceptance and Session establishment as verified, while explicitly stating that Provider Integration is not proven.
- The primary receipt supporting that later Credential/Session verification was not found in the current worktree. An older integration note instead records an activation failure; the two records therefore describe different scopes or times and must not be merged into a current-session claim.
- No Choice-specific Evidence Manifest or Research Runtime consumer was found.

**Boundary**

Choice has the strongest historical session evidence of the three providers, but only as a **secondary governance record** in this audit. Current Session, real Evidence generation, Manifest binding, and Research Runtime capability remain **UNKNOWN / NOT PROVEN**. Status is **PARTIAL / NOT CLAIMED**.

### 4.3 iFinD

**Observed**

- `scripts/ifind_data.py` and the `ths_query` MCP entry exist.
- An older integration record observed the server SDK and a successful Python import, followed by login failure due to API permission.
- A read-only local module lookup on 2026-07-31 returned `iFinDPy: NOT_FOUND`.
- No iFinD-specific Evidence Manifest or Research Runtime consumer was found.

**Preserved historical boundary**

```text
Transport: CONNECTED
Provider: AVAILABLE (limited)
Evidence Integration: TO VERIFY
Production Research Capability: NOT CLAIMED
```

This historical boundary is not a current credential or session receipt. Current Credential and Session remain **UNKNOWN**; Evidence Integration remains **TO VERIFY**.

## 5. Runtime Consumer Mapping

```text
Wind entry
  -> scripts/wind_data.py
  -> wind_query / gateway code
  -> direct MCP invocation
  -X-> no verified Research Runtime binding

Choice entry
  -> scripts/emquant_data.py
  -> emquant_query
  -> direct MCP invocation
  -X-> no verified Evidence Manifest or Research Runtime binding

Choice shadow path
  -> fixture data
  -> scripts/choice_provider.py normalization
  -> shadow smoke
  -X-> not live provider evidence

iFinD entry
  -> scripts/ifind_data.py
  -> ths_query
  -> direct MCP invocation
  -X-> no verified Evidence Manifest or Research Runtime binding
```

Direct tool availability proves an invocation surface only. It does not prove that Research Runtime consumes admitted evidence from that provider.

## 6. Capability Claim Findings

1. `docs/ifind_emquant_integration.md` uses broad integration language while its own evidence records authentication/activation limits and future integration work. Treat it as an implementation-history note, not a current capability receipt.
2. MCP tool names and multi-source gateway code establish code paths, not live sessions or production research capability.
3. The Choice Credential/Session state is retained as historically verified because the effective Capability Claim Matrix records it. Since the primary receipt is absent from this worktree, it must not be upgraded to a current Session claim.
4. No inspected provider has a proven complete chain of Adapter -> Evidence Manifest -> Research Runtime Consumer.
5. No inspected provider may be described as production ready or as an established institutional research capability.

## 7. Capability Boundary

```text
Code exists
  != Credential exists
  != Session established
  != Evidence generated
  != Evidence admitted by Manifest/QC
  != Research Runtime capability
  != Production capability
```

## 8. Audit Restrictions Observed

- No Wind, Choice, or iFinD connection was attempted.
- No credential or token was read, stored, or changed.
- No SDK was installed or imported for authentication.
- No Provider Adapter, Runtime, Trust Gate, or Capability Matrix was modified.
- No synthetic evidence was used to fill a missing live link.
- No production service or configuration was changed.

## 9. Reconciliation Decision

```text
Provider Evidence Reconciliation: COMPLETE
Provider Integration: NOT CHANGED
Current Provider Sessions: NOT PROBED
Evidence Manifest Binding: NOT PROVEN
Research Runtime Capability: NOT CLAIMED
Production Capability: NOT CLAIMED
```

This audit calibrates repository claims only. Any future capability promotion requires a separately authorized, provider-specific evidence window with credential loading, session proof, real evidence retrieval, Manifest/QC binding, and Runtime Consumer validation.
