# Intent / Routing / Fallback Runtime (P4 Boundary)

This directory is the **Intent Runtime boundary** under ADR-003 (file-level).

**Phase A status**: boundary placeholder only.

## Forbidden in Phase A

No implementation files permitted:

- No `router.py` / `runtime.py` / `executor.py`
- No `intent/classifier.py` / `intent/qc.py` / `routing/router.py` etc.
- No `runtime_events.jsonl`

Phase A only establishes the directory. Implementation starts in Phase E.
See `docs/intent_routing_fallback_runtime_implementation_plan_v0.md` §3.
