"""Research runtime session state."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .events import RuntimeEvent, RuntimeEventLog, utc_now_iso


@dataclass
class ResearchSession:
    symbol: str
    session_id: str = field(default_factory=lambda: f"research-{uuid.uuid4().hex[:12]}")
    state: str = "INIT"
    provider: str | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    qc: dict[str, Any] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    event_log: RuntimeEventLog = field(default_factory=RuntimeEventLog)

    @property
    def events(self) -> list[RuntimeEvent]:
        return self.event_log.events

    def add_event(self, type: str, message: str, payload: dict[str, Any] | None = None) -> RuntimeEvent:
        self.updated_at = utc_now_iso()
        return self.event_log.append(
            RuntimeEvent(
                event_id=len(self.events) + 1,
                session_id=self.session_id,
                type=type,
                message=message,
                payload=payload or {},
            )
        )

    def set_state(self, state: str, message: str | None = None) -> None:
        self.state = state
        self.add_event("state_entered", message or f"Entered {state}", {"state": state})

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "symbol": self.symbol,
            "state": self.state,
            "provider": self.provider,
            "evidence": self.evidence,
            "context": self.context,
            "qc": self.qc,
            "artifact_paths": self.artifact_paths,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": self.event_log.to_list(),
        }
