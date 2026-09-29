# Task Authorization Boundary — Implementation Receipt

**Status**: IMPLEMENTED (working tree) — NOT COMMITTED (commit authorization for this unit is separate from implementation authorization)
**Author**: StressTestExecutor (Claude Sonnet 4.6)
**Date**: 2026-09-29
**Authority**: Owner AdJ 2026-09-29 §B — "TASK_AUTHORIZATION_BOUNDARY_IMPLEMENTATION = AUTHORIZED AS SEPARATE UNIT"
**Design artifact**: `docs/design/task_authorization_boundary_design_v0.md` (committed @52b8224)

---

## 0. Scope

Per Owner AdJ §B: "Implement only: requested_use × allowed_use → AUTHORIZED | BLOCKED."

Deliverables this round:
1. `research_runtime/task_authorization.py` — pure `authorize_task()` function (NEW)
2. `mcp_server.py::stock_analysis` — boundary wired after Evidence Admission, before LLM consumer (MODIFIED, surgical)
3. `tests/test_task_authorization.py` — 15 unit tests (NEW)

---

## 1. The function

```python
def authorize_task(requested_use, allowed_use) -> bool:
    # True = AUTHORIZED, False = BLOCKED. Fail closed.
    if not isinstance(requested_use, str):
        return False
    requested = requested_use.strip()
    if not requested:
        return False
    if not isinstance(allowed_use, (list, tuple, set, frozenset)):
        return False
    if not allowed_use:
        return False
    return requested in allowed_use
```

Semantics — exact set membership, deterministic, no LLM / no fuzzy / no substring / no embedding.

| requested_use | allowed_use | result |
|---|---|---|
| `fundamental_overview` | `["fundamental_overview"]` | AUTHORIZED |
| `position_sizing` | `["fundamental_overview"]` | BLOCKED (SYN-010) |
| `target_price` | `["fundamental_overview","event_extraction"]` | BLOCKED (SYN-011) |
| `fundamental_overview` | `[]` | BLOCKED |
| `None` / `""` / non-str | any | BLOCKED (fail closed) |
| any | `None` / non-collection | BLOCKED (fail closed) |

---

## 2. Wiring position

`mcp_server.py::stock_analysis` (now `stock_analysis(query, requested_use=None)`):

```
Evidence Admission:  bundle = _admit_for_stock_analysis(data, qc=qc)   # build_evidence_bundle
  ├─ if BlockedEvidence → _make_error_response (unchanged)
  └─ Task Authorization: if not authorize_task(requested_use, bundle.allowed_use)
        → _make_error_response("task_authorization_blocked: ...")      # NEW
LLM-facing Consumer: formatted = format_stock_analysis_from_bundle(...) # unchanged
```

The boundary executes unconditionally between admission and the consumer.
Fail-closed: `requested_use=None` (undetermined) → `authorize_task` returns False → BLOCK.

---

## 3. Hard constraints verification

| Constraint | Status | Evidence |
|---|---|---|
| DO NOT modify build_evidence_bundle semantics | ✅ SATISFIED | `research_runtime/evidence_bundle.py` untouched this session (its pre-existing uncommitted diff is from prior Unit 1 closure work, not this unit) |
| DO NOT create a second Evidence Admission authority | ✅ SATISFIED | `authorize_task` is a pure read-only predicate; it does not call `build_evidence_bundle`, does not produce `EvidenceBundle`/`BlockedEvidence` |
| DO NOT change provider/QC/freshness/provenance policy | ✅ SATISFIED | No changes to `_classify_provider`, `_allowed_use`, `_status`, freshness mapping, or provenance code |
| DO NOT remediate MX-DS/iFinD | ✅ SATISFIED | No changes to `scripts/mxds_data.py`, iFinD wiring, or provider chain |
| DO NOT modify P4 | ✅ SATISFIED | No P4 code touched |
| Fail closed when requested_use cannot be determined or exceeds allowed_use | ✅ SATISFIED | `authorize_task` returns False on None/empty/non-str and on non-membership; MCP layer returns fail-closed error |
| Task Authorization must be mechanical | ✅ SATISFIED (interpretation) | Pure deterministic set-membership; no probabilistic/LLM/substring match. (Owner's sentence was truncated at "mechanically"; interpreted as "mechanically enforced" per design doc v0 §2.4/§6.) |

---

## 4. Test results

```
$ python3.11 -m pytest tests/test_task_authorization.py -v
15 passed in 0.03s
```

| Test | Covers |
|---|---|
| test_subset_membership_authorized | requested ∈ allowed |
| test_membership_among_multiple_authorized | membership in list |
| test_superset_request_blocked_syn010 | SYN-010 counterexample |
| test_superset_request_blocked_syn011 | SYN-011 counterexample |
| test_trading_decision_fields_never_authorized | short_term_signal/fund_flow/position_sizing/buy_sell_recommendation never authorized |
| test_empty_allowed_use_blocked | empty allowed_use → BLOCK |
| test_none_requested_use_fail_closed | None → BLOCK |
| test_empty_string_requested_use_fail_closed | "" → BLOCK |
| test_whitespace_only_requested_use_fail_closed | "   " → BLOCK |
| test_non_str_requested_use_fail_closed | int / list → BLOCK |
| test_none_allowed_use_fail_closed | None allowed_use → BLOCK |
| test_str_allowed_use_not_substring_matched | no substring trap |
| test_whitespace_stripped | normalization |
| test_case_sensitive_exact | no case folding |
| test_integration_real_allowed_use_blocks_position_sizing | real build_evidence_bundle bundle → SYN-010 semantics |

---

## 5. Residual integration gap (flag to Owner)

The MCP tool `stock_analysis` previously took only a ticker `query`. It has no way to infer the user's *task intent* from that query. This boundary therefore adds an explicit `requested_use` parameter to the tool signature.

Consequence: **with the boundary wired fail-closed, a call that omits `requested_use` now returns `task_authorization_blocked`.** The finance-suite skill (the LLM-facing caller) must be updated to pass `requested_use` derived from the user's prompt. That skill update is **out of scope** for this unit and is NOT yet done.

This is the intended effect of closing the PRODUCTION_GAP (TASK_AUTHORIZATION_NOT_ENFORCED). If the Owner prefers a non-breaking rollout (boundary bypassed while `requested_use` is absent), that is a deliberate deviation from "fail closed" and requires a separate Owner decision.

---

## 6. SHAs (working tree)

```text
138f000643e87ab946b3ae7f86ff532ad173debd4b71372d055b6758a15d8ebe  research_runtime/task_authorization.py
02a893c839fb5bd20132a6286708db93f1bde689dea20a100ec785924630f155  tests/test_task_authorization.py
0288b014a56a5973592fd891c4b80f3c1540e49300a9e87dd3bb32e29e054544  mcp_server.py  (contains prior Unit 1 closure + this boundary)
```

---

## 7. Commit status

- Part A (Owner AdJ §A): 4 reviewed artifacts committed @ `52b8224` ✅
- Part B (this unit): IMPLEMENTED, **NOT committed** — mcp_server.py already carries uncommitted prior Unit 1 closure changes; committing the boundary cleanly requires either (a) Owner authorization to commit mcp_server.py as a whole (Unit 1 closure + boundary), or (b) a staged commit separating the boundary diff from the prior closure diff.

---

## 8. NEXT_OWNER_DECISION

1. Whether to commit the boundary unit (task_authorization.py + tests + mcp_server.py boundary wiring).
2. Whether the fail-closed-on-`None` behavior is accepted, or a non-breaking rollout is preferred (deviation from "fail closed").
3. Whether the finance-suite skill's `requested_use` plumbing is authorized as the follow-up integration step.

STOP. No further mutation without Owner authorization.
