# Direction 2 Entry Condition — Bounded Read-only Production Path Trace v0.1

**Date:** 2026-08-09
**Status:** `SPECIFIED — NOT EXECUTED`
**Authority:** Entry-condition specification only. Does not authorize execution.
**Predecessor:** `TRUST_GATE_RUNTIME_PATH_RECONCILIATION_REVIEW_v0.1` (Type C, evidence-relative)
**Successor (blocked on this):** Architecture Integration Design window

---

## 0. Why this exists

The Reconciliation Review classified the gap as Type C **within static scope**, and explicitly
listed model-mediated tool selection as uninspected. Architecture Integration Design cannot
start on top of that ambiguity: if the design assumes a static Flask→provider chain but
production research requests actually travel a model-mediated path, the chosen enforcement
boundary is wrong by construction.

This entry condition resolves exactly one question — **which path does a research request
take** — and is forbidden from resolving any other.

---

## 1. The load-bearing constraint

This trace must be **designed so it cannot produce enforcement evidence, even accidentally.**

That is not a stylistic preference. If the producer observes gate decisions while tracing the
path, that observation:

- was not adversarially selected,
- carries no baseline disclosure,
- was produced by the party who will later build the integration,

and therefore contaminates the Runtime Enforcement Observation window (Step 4) it would appear
to help. The contamination is silent: nobody has to lie, the evidence just arrives pre-loaded
with the producer's expectations.

So the trace is bounded **by construction**, not by discipline:

```
Observable by design:     which modules/handlers execute for a request
Not observable by design: what decision any gate emitted
```

If the chosen trace method can see gate verdicts, the method is wrong — pick a narrower one.

---

## 2. Question boundary

### 2.1 In scope — Path Observation

```text
Q-P1  What process serves the research request? (binary/module identity)
Q-P2  What is the ingress → handler chain?
Q-P3  Does the handler reach a provider synchronously, or hand off to a model-mediated step?
Q-P4  If model-mediated: what is the tool-dispatch surface the model selects from?
Q-P5  Which of the 4 gate candidates, if any, is importable from the serving process?
```

Q-P5 is deliberately phrased as **importable**, not **invoked**. Import reachability is a path
property. Invocation is an enforcement property and belongs to Step 4.

### 2.2 Out of scope — Enforcement Observation

```text
❌ Did the gate emit a decision?
❌ Was any field blocked?
❌ Did stale data get through?
❌ Does G3 fire on T+N?
❌ Is the envelope rebuilt on BLOCK?
```

Any of these appearing in the trace output means the trace exceeded its mandate and the
resulting artifact is **not admissible** as a design input.

---

## 3. Method constraints

| Constraint | Rule |
|---|---|
| Mutation | None. No deploy, no restart, no git operation, no config edit. |
| Request generation | Prefer **zero** synthetic requests. If unavoidable, one non-mutating request, logged, disclosed. |
| Data handling | Provider payload contents are not recorded — only the module path they traversed. |
| Credential exposure | Reference secrets by key name only; never echo values. |
| Scope creep guard | Trace terminates at the first provider boundary. It does not follow provider responses back. |

The "no payload contents" rule is what keeps this from becoming an enforcement observation: if
you never record what the data *was*, you cannot accidentally record whether it *should have
been blocked*.

---

## 4. The trace's own claim boundary

The trace inherits the same discipline it was created to enforce. One traced request proves one
path for one request class.

Required in the output artifact:

```text
traced_request_classes:  [ ... enumerated ... ]
untraced_request_classes: [ ... enumerated ... ]
claim: "Request class X reaches provider via path P"
NOT:   "All research requests reach provider via path P"
```

A single-request trace generalized to "the production research path" would reproduce, one layer
up, exactly the observed-absence→universal-absence error the Reconciliation Review was corrected
for.

---

## 5. Exit criteria

This entry condition is satisfied when **all** hold:

- [ ] Serving process identity recorded (Q-P1)
- [ ] Ingress → handler chain recorded (Q-P2)
- [ ] Static vs model-mediated determination recorded (Q-P3)
- [ ] If model-mediated: tool-dispatch surface enumerated (Q-P4)
- [ ] Gate candidate import-reachability recorded (Q-P5)
- [ ] Traced / untraced request classes enumerated (§4)
- [ ] Zero enforcement observations present in the artifact (§2.2 audit)

Output: `PRODUCTION_PATH_TRACE_v0.1` — evidence class **Path Observation**, not Capability Evidence.

Not required for satisfaction: gate invocation, gate correctness, coverage of all request classes.

---

## 6. Known blocker

Per `TRUST_GATE_RUNTIME_VALIDATION_GOVERNANCE_REVIEW_v0.1` (2026-08-09), SSH access to the
production host is **BLOCKED (fail2ban)**, requiring human action via the Tencent Cloud Console.

Consequence: this entry condition is **SPECIFIED but NOT EXECUTABLE** at time of writing.
Architecture Integration Design therefore remains blocked — not on authorization, but on
observability.

Honest statement of the chain:

```
fail2ban unban (human)
    → Environment Identity Confirmation (4 read-only commands)
    → Bounded Read-only Path Trace  ← THIS DOCUMENT
    → Architecture Integration Design
    → Implementation Authorization
    → Deployment Identity
    → Runtime Enforcement Observation
    → Capability Claim
```

Nothing downstream of the unban is executable today.

---

## 7. What this document does not authorize

```
❌ Executing the trace
❌ SSH access attempts beyond the already-blocked state
❌ Any probe (stale, G3, provider)
❌ Any implementation or commit
❌ Any capability claim, including conditional
❌ Starting Architecture Integration Design
```

---

## 8. Declaration

| Field | Value |
|---|---|
| Status | `SPECIFIED — NOT EXECUTED` |
| Evidence class produced | Path Observation (when executed) |
| Capability effect | `NONE` |
| Implementation | `NOT AUTHORIZED` |
| Blocker | SSH access (fail2ban) — human action required |
| Defers to | `EVIDENCE_GOVERNANCE_v1.0`, `TRUST_GATE_RUNTIME_PATH_RECONCILIATION_REVIEW_v0.1` |

**This document does not assert** that the production path is known, that any gate is
integrated, or that Architecture Integration Design may begin.
