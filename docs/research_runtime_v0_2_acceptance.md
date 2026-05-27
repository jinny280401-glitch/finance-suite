# Research Runtime v0.2 Acceptance

**Date:** 2026-05-28  
**Status:** Accepted

---

## Verification Results

| Check | Result |
|-------|--------|
| `python3 smoke_research_runtime.py` | ✅ ok=true, final_state=DONE, event_count=11 |
| `python3 smoke_research_runtime_gateway.py` | ✅ ok=true, provider=finance_data_gateway, qc_passed=true |
| `python3 -m compileall research_runtime/` | ✅ No compile errors |
| `/tmp/research_runtime_latest.json` exists | ✅ |
| `/tmp/research_runtime_events.jsonl` exists | ✅ 11 events |
| final_state == DONE | ✅ |
| qc_passed == true | ✅ |

---

## Artifacts

| Artifact | Path |
|----------|------|
| Latest session snapshot | `/tmp/research_runtime_latest.json` |
| Event log | `/tmp/research_runtime_events.jsonl` |
| Smoke test (local) | `smoke_research_runtime.py` |
| Smoke test (gateway) | `smoke_research_runtime_gateway.py` |

---

## v0.2 Capability Boundary

### Included

- **Session layer** (`research_runtime/session.py`)  
  `ResearchSession` with `session_id`, `state`, `provider`, `evidence`, `context`, `qc`, `artifact_paths`

- **Events layer** (`research_runtime/events.py`)  
  `RuntimeEvent` + `RuntimeEventLog`, writes `/tmp/research_runtime_events.jsonl`

- **Workflow layer** (`research_runtime/workflow.py`)  
  `run_research_workflow(symbol, mode)` — state machine: INIT → STARTED → PROVIDER_SELECTION → EVIDENCE_RETRIEVAL → CONTEXT_BUILDING → QC → DONE

- **Gateway online path** (`mode="gateway"`)  
  Calls `finance_data_gateway.get_finance_data("quote", symbol)` via the existing provider chain (Wind → Tushare → JoinQuant → AkShare → cache)

- **Gateway offline fallback** (`mode="local"`)  
  Returns `local_research_stub` evidence — no network calls, no LLM

### Not Included

- Production router (`/api/analyze` or any `finance-suite-web` route)
- Frontend UI changes
- New `data_type` values beyond `quote`
- New data providers
- LLM calls
- Finance Data Gateway contract changes

---

## Source Files

```
research_runtime/__init__.py
research_runtime/events.py
research_runtime/session.py
research_runtime/workflow.py
scripts/finance_data_contract.py   (Data Gateway v0, unchanged)
scripts/finance_data_gateway.py    (Data Gateway v0, unchanged)
smoke_research_runtime.py
smoke_research_runtime_gateway.py
docs/data_gateway_v0.md            (Data Gateway v0 docs, unchanged)
```

---

## Next Phase

**v0.3** — not started in this round.

Candidate scope (to be decided separately):
- Multi-symbol batch mode
- Structured research context output
- Event streaming to a persistent store
