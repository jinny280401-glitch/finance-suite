# Research Runtime v0

Research Runtime is the local execution layer for Finance Suite research
workflows. It is intentionally separate from production routes, frontend UI,
real LLM calls, and the Finance Data Gateway contract.

## v0.2 Events

v0.2 adds runtime observability. Every local research workflow now records a
structured event stream that explains what happened, in what order, and with
which lightweight payloads.

Artifacts:

- `/tmp/research_runtime_latest.json`
- `/tmp/research_runtime_events.jsonl`

Event types:

- `state_entered`
- `provider_selected`
- `evidence_retrieved`
- `context_built`
- `qc_completed`
- `artifact_written`
- `workflow_completed`
- `workflow_failed`

## Why Events Exist

Research workflows are multi-step. A final artifact can tell us the result, but
it cannot easily explain whether a provider was selected, evidence was found,
context was built, or QC failed before output. Events make the workflow
traceable without requiring a UI or live LLM integration.

For local debugging, the JSONL artifact is the fastest way to answer:

- Which phase ran last?
- Which provider was selected?
- How much evidence was retrieved?
- Did QC pass before writing artifacts?
- Did the workflow fail, and with what error?

## Runtime Panel Follow-Up

A future Runtime Panel can read `/tmp/research_runtime_events.jsonl` as an
append-only timeline:

1. Load each JSONL row as one event.
2. Group rows by `session_id`.
3. Render `type`, `message`, `created_at`, and selected `payload` fields.
4. Read `/tmp/research_runtime_latest.json` for the latest session summary,
   final state, evidence count, QC result, and artifact paths.

The panel does not need to understand provider internals. It only needs the
event stream and the latest session snapshot.

## Events vs Evidence

Events describe the workflow execution.

Examples:

- provider selected
- evidence retrieval finished
- context built
- QC completed
- artifact written

Evidence describes material gathered for research.

Examples:

- a Finance Data Gateway quote response
- a research scope stub
- a skeleton section list

Events answer "what happened during the run?" Evidence answers "what material
did the run collect?" Keeping them separate makes the runtime easier to debug
and keeps research facts from being mixed with execution telemetry.

## Non-Goals

v0.2 does not:

- modify production routes
- change the Finance Data Gateway contract
- connect frontend UI
- call a real LLM
- generate investment advice
