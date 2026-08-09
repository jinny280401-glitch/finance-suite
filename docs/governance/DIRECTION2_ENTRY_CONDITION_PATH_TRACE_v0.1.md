# Direction 2 Entry Condition — Bounded Read-only Production Path Trace v0.1

**Date:** 2026-08-09
**Status:** `SPECIFIED — NOT EXECUTED`
**Authority:** Entry-condition specification only. Does not authorize execution.
**Predecessor:** `TRUST_GATE_RUNTIME_PATH_RECONCILIATION_REVIEW_v0.1` (Type C, evidence-relative)
**Successor (blocked on this):** Architecture Integration Design window
**Scope note:** This document specifies the full entry gate. The Bounded Read-only Path Trace is
Step 3 of that gate, not the whole gate.

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

## 0.5 Two prerequisites before the trace

The Bounded Read-only Path Trace (§2–§5) is **Step 3** of the Architecture Integration Design
entry gate. Two preceding steps must be satisfied first.

### 0.5.1 Step 1 — Baseline Identity Confirmation

Answer:

```text
What exact artifact was reconciled in the frozen review?
```

Required outputs:

- Commit hash of the inspected corpus at reconciliation time
- Dirty-working-tree disclosure (untracked / modified files)
- Pin the freeze declaration to that baseline

Known gap: the Reconciliation Review inspected `cd6bdb9` plus a dirty working tree
(`trust_gate/` untracked, `mcp_server.py` modified), but the freeze declaration does not yet
pin that baseline. This step fixes that disclosure defect before any new evidence is collected.

### 0.5.2 Step 2 — Production artifact reconciliation

Bind the inspected corpus to the production runtime.

Observed production artifact: `/home/ubuntu/finance-suite-web/app.main:app`
Inspected corpus: local `finance-suite` repo

Required outputs (read-only):

```text
Q-A1  whoami / hostname / pwd on production host
Q-A2  What process serves app.main:app? (PID, binary, working directory)
Q-A3  What service/unit manages it? (systemd, supervisor, docker, etc.)
Q-A4  What is the nginx ingress → upstream mapping?
Q-A5  What git commit / artifact version is deployed at /home/ubuntu/finance-suite-web?
Q-A6  Is the deployed artifact derived from the inspected corpus? If so, by what mapping?
```

Until Q-A5 and Q-A6 are answered, **the design target is unknown**. Designing a Gate integration
against the local repo while production runs a different artifact is the failure mode this step
prevents.

### 0.5.3 Why these precede the path trace

```text
Baseline Identity            → "what object did we reason about?"
Production artifact reconciliation → "what object actually runs?"
Bounded Read-only Path Trace → "what path does a request take in that object?"
Architecture Integration Design → "where can enforcement be placed without bypass?"
```

Skipping the first two turns the third into a fixture observation of the wrong system.

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

### 5.1 Step 3 exit criteria (Bounded Read-only Path Trace)

The path trace is satisfied when **all** hold:

- [ ] Serving process identity recorded (Q-P1)
- [ ] Ingress → handler chain recorded (Q-P2)
- [ ] Static vs model-mediated determination recorded (Q-P3)
- [ ] If model-mediated: tool-dispatch surface enumerated (Q-P4)
- [ ] Gate candidate import-reachability recorded (Q-P5)
- [ ] Traced / untraced request classes enumerated (§4)
- [ ] Zero enforcement observations present in the artifact (§2.2 audit)

Output: `PRODUCTION_PATH_TRACE_v0.1` — evidence class **Path Observation**, not Capability Evidence.

Not required for satisfaction: gate invocation, gate correctness, coverage of all request classes.

### 5.2 Full Architecture Integration Design entry gate

Architecture Integration Design may begin only when **all three** preceding steps are satisfied:

- [ ] Step 1 — Baseline Identity Confirmation (§0.5.1)
- [ ] Step 2 — Production artifact reconciliation (§0.5.2)
- [ ] Step 3 — Bounded Read-only Path Trace (§5.1)

---

## 6. Known blocker

**Current blocker:** Production artifact ↔ inspected corpus reconciliation pending.

**Observability constraint:** SSH access instability / environment access path unresolved.

SSH/WebShell recovery is an infrastructure action that restores evidence-collection capability.
It is **not** Trust Gate advancement. The Trust Gate window resumes only after the production
artifact is reconciled with the inspected corpus.

Consequence: this entry condition is **SPECIFIED but NOT EXECUTABLE** at time of writing.
Architecture Integration Design therefore remains blocked — not on authorization, but on
**not yet knowing the design target**.

Honest statement of the chain:

```
P0  Restore stable observability (SSH/WebShell — human action)
        ↓
P1a Baseline Identity Confirmation                ← Step 1
        ↓
P1b Production artifact reconciliation            ← Step 2
        ↓
P1c Bounded Read-only Path Trace                  ← Step 3, THIS DOCUMENT
        ↓
P2  Architecture Integration Design
        ↓
    Implementation Authorization
        ↓
    Deployment Identity
        ↓
    Runtime Enforcement Observation
        ↓
    Capability Claim
```

Nothing downstream of P1b is executable today.

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
| Evidence class produced | Path Observation (when Step 3 executed) |
| Capability effect | `NONE` |
| Implementation | `NOT AUTHORIZED` |
| Blocker | Production artifact ↔ inspected corpus reconciliation pending |
| Observability constraint | SSH access instability / environment access path unresolved |
| Defers to | `EVIDENCE_GOVERNANCE_v1.0`, `TRUST_GATE_RUNTIME_PATH_RECONCILIATION_REVIEW_v0.1` |

**This document does not assert** that the production path is known, that any gate is
integrated, or that Architecture Integration Design may begin.
