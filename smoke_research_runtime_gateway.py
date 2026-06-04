"""Smoke test for Research Runtime v0.2 with Finance Data Gateway evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from research_runtime import run_research_workflow


EVENTS_ARTIFACT = Path("/tmp/research_runtime_events.jsonl")


def main() -> int:
    session = run_research_workflow(symbol="300750.SZ", mode="gateway")
    event_count = len(session.events)
    out = {
        "session_id": session.session_id,
        "final_state": session.state,
        "provider": session.provider,
        "evidence_count": len(session.evidence),
        "event_count": event_count,
        "qc_passed": session.qc.get("passed") is True,
        "trust_gate": session.context.get("trust_gate", {}),
        "events_artifact_exists": EVENTS_ARTIFACT.exists(),
    }
    trust_gate = out["trust_gate"]
    has_allowed_evidence = out["evidence_count"] > 0 and out["qc_passed"] is True
    has_blocked_gateway_response = (
        out["evidence_count"] == 0
        and out["qc_passed"] is False
        and trust_gate.get("blocked_count", 0) > 0
        and trust_gate.get("has_any_allowed") is False
    )
    out["ok"] = (
        out["final_state"] == "DONE"
        and out["provider"] == "finance_data_gateway"
        and out["event_count"] > 0
        and (has_allowed_evidence or has_blocked_gateway_response)
        and out["events_artifact_exists"] is True
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
