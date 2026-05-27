"""Local Research Runtime workflow v0.2."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .session import ResearchSession


LATEST_ARTIFACT = Path("/tmp/research_runtime_latest.json")
EVENTS_ARTIFACT = Path("/tmp/research_runtime_events.jsonl")


def _ensure_scripts_path() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))


def _select_provider(mode: str) -> str:
    return "finance_data_gateway" if mode == "gateway" else "local_research_stub"


def _retrieve_evidence(symbol: str, provider: str) -> list[dict[str, Any]]:
    if provider == "finance_data_gateway":
        _ensure_scripts_path()
        import finance_data_gateway

        quote = finance_data_gateway.get_finance_data("quote", symbol=symbol)
        return [{
            "kind": "gateway_quote",
            "source": quote.get("provider") or "finance_data_gateway",
            "ok": quote.get("ok"),
            "as_of": quote.get("as_of"),
            "payload": quote,
        }]

    return [
        {
            "kind": "research_scope",
            "source": "local_research_stub",
            "payload": {
                "symbol": symbol,
                "scope": "enterprise_and_industry_research",
                "note": "Local runtime smoke evidence; no LLM and no investment advice.",
            },
        },
        {
            "kind": "skeleton",
            "source": "research_editorial_layer",
            "payload": {"sections": [f"{i:02d}" for i in range(11)]},
        },
    ]


def _build_context(session: ResearchSession) -> dict[str, Any]:
    return {
        "symbol": session.symbol,
        "provider": session.provider,
        "evidence_count": len(session.evidence),
        "research_question": "Build a traceable research navigation context without recommendations.",
        "llm_enabled": False,
    }


def _complete_qc(session: ResearchSession) -> dict[str, Any]:
    evidence_count = len(session.evidence)
    return {
        "passed": evidence_count > 0,
        "status": "success" if evidence_count > 0 else "failure",
        "evidence_count": evidence_count,
        "checks": {
            "has_session_id": bool(session.session_id),
            "has_provider": bool(session.provider),
            "has_evidence": evidence_count > 0,
            "llm_not_used": True,
        },
    }


def _write_artifacts(session: ResearchSession) -> None:
    session.artifact_paths = {
        "latest": str(LATEST_ARTIFACT),
        "events": str(EVENTS_ARTIFACT),
    }
    session.add_event("artifact_written", "Runtime artifact paths prepared", session.artifact_paths)
    session.add_event("workflow_completed", "Research workflow completed", {
        "state": "DONE",
        "qc_passed": session.qc.get("passed") is True,
        "evidence_count": len(session.evidence),
    })
    session.state = "DONE"
    session.updated_at = session.events[-1].created_at if session.events else session.updated_at

    LATEST_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    LATEST_ARTIFACT.write_text(json.dumps(session.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    session.event_log.write_jsonl(EVENTS_ARTIFACT)


def run_research_workflow(symbol: str = "300750.SZ", mode: str = "local") -> ResearchSession:
    """Run a local, observable research workflow without real LLM calls."""
    session = ResearchSession(symbol=symbol)
    try:
        session.set_state("STARTED", "Research workflow started")

        session.set_state("PROVIDER_SELECTION", "Selecting research data provider")
        session.provider = _select_provider(mode)
        session.add_event("provider_selected", "Provider selected", {
            "provider": session.provider,
            "mode": mode,
        })

        session.set_state("EVIDENCE_RETRIEVAL", "Retrieving evidence")
        session.evidence = _retrieve_evidence(symbol, session.provider)
        session.add_event("evidence_retrieved", "Evidence retrieved", {
            "evidence_count": len(session.evidence),
            "evidence_kinds": [item.get("kind") for item in session.evidence],
        })

        session.set_state("CONTEXT_BUILDING", "Building research context")
        session.context = _build_context(session)
        session.add_event("context_built", "Research context built", session.context)

        session.set_state("QC", "Completing runtime QC")
        session.qc = _complete_qc(session)
        session.add_event("qc_completed", "Runtime QC completed", session.qc)

        _write_artifacts(session)
        return session
    except Exception as exc:
        session.qc = {"passed": False, "status": "failure", "error": str(exc)}
        session.state = "FAILED"
        session.add_event("workflow_failed", "Research workflow failed", {"error": str(exc)})
        session.artifact_paths = {"latest": str(LATEST_ARTIFACT), "events": str(EVENTS_ARTIFACT)}
        LATEST_ARTIFACT.write_text(json.dumps(session.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        session.event_log.write_jsonl(EVENTS_ARTIFACT)
        return session
