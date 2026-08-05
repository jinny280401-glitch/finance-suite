# Organization-Level Agent Harness — Evidence Remediation Plan v0.1

**Status:** REFERENCE ONLY. NOT ADOPTED. NOT ARCHITECTURE DECISION. NOT GOVERNANCE BASELINE.
**Date:** 2026-08-05
**Window:** Evidence remediation — Phase 1 research outputs require downgrade of unverified synthesis claims before any future window can consume them as input.
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

---

## 1. Research question retained

> Are the morning's governance frictions **process design problems** that better procedures can solve, OR are they **evidence that future Agent systems require an organizational-level Harness as native infrastructure**?

This question is preserved as a valid research question. The Phase 1 research outputs provide external reference patterns. They do **not** provide a verified answer about the Finance Suite runtime. The question remains open for future evidence-gathering windows.

---

## 2. Existing claims requiring validation

The following claims appeared in the Synthesis v0.1 original wording and have been downgraded in this remediation. They are recorded here so future windows know what was corrected and why.

### 2.1 "Both — but with the substrate primary"

**Original claim:** The four reports converge that seven of eight morning frictions are substrate-primary. Procedure overlays add discipline but cannot substitute for substrate separation.

**Why downgraded:** The four research reports describe patterns observed in **external** systems (industry products, open-source projects, governance literature, software-org practice). They did **not** inspect the Finance Suite runtime directly. A claim that external patterns prove a local substrate gap is an unverified inference. The research can observe that external patterns are *consistent with* the morning's frictions; it cannot conclude *causation* or *necessity*.

**Remediated to:** "Research suggests potential runtime governance gaps. Further validation required."

### 2.2 "Industry treats the substrate separation as native infrastructure"

**Original claim:** Implied that industry consensus requires substrate-level harness as the correct answer.

**Why downgraded:** The Industry report cites products that offer substrate-level primitives (Entra, Bedrock AgentCore, A2A). Product existence is not industry consensus. "Vendor X offers feature Y" does not imply "Finance Suite requires feature Y." The original wording risked being read as an architecture recommendation smuggled through research language.

**Remediated to:** "Industry references describe substrate separation as infrastructure in some production systems, not as a universal necessity."

### 2.3 Friction classification: "H-primary" (substrate-primary)

**Original claim:** The friction-by-friction table classified seven of eight frictions as H-primary (substrate) with P-overlay (procedure).

**Why downgraded:** The H/P classification was performed by the Synthesizer based on external reports, not by inspecting the Finance Suite runtime. A classification derived from external patterns applied to local frictions is a *hypothesis*, not a finding. The table classification is preserved as a reference observation; the normative conclusion ("substrate-primary") is removed.

**Remediated to:** "The four research reports classified seven of eight morning frictions as primarily associated with substrate-level patterns observed in external systems. This classification is a research observation, not a verified finding."

---

## 3. Evidence gaps

The Phase 1 Closure Review (`ORG_LEVEL_AGENT_HARNESS_PHASE1_CLOSURE_REVIEW.md`) identified the following gaps. This remediation plan inherits them as its work list.

### 3.1 Missing SOURCE_MATRIX.md (Condition 2)

**Gap:** No consolidated `SOURCE_MATRIX.md` exists. Each agent report contains its own source index, but citations, capability verdicts, and evidence gaps are not consolidated.

**Required by:** Task card and C Phase 1 method note.

**Status of remediation:** An untracked `ORG_LEVEL_HARNESS_SOURCE_MATRIX_v0.1.md` exists in the working tree (observed 2026-08-05). It has not been committed, reviewed, or verified against the acceptance criteria.

**Next action:** Review the existing untracked Source Matrix. If it passes read-only verification (all 4 reports covered, capability verdicts present, evidence gaps enumerated), commit it. If incomplete, document the gaps and produce a v0.2.

### 3.2 Capability classification (Partial Pass)

**Gap:** The distinction between Documented / Implemented / Tested / Operationally Proven is present in prose but not encoded as structured verdicts per candidate.

**Required by:** Task card §8 (C method note): ranked source shortlist with explicit capability verdicts.

**Next action:** Source Matrix must include a `capability_verdict` column per candidate with values from: `PROVEN` / `PARTIAL` / `NOT PROVEN` / `UNKNOWN`. Prose distinction in individual reports is insufficient for downstream consumption.

### 3.3 Synthesis overstatement (this remediation)

**Gap:** Synthesis v0.1 original wording converted external pattern observation into implied substrate necessity.

**Status:** RESOLVED by this remediation. Synthesis §0 and §3.9 downgraded from normative claims to research observations.

**Verification:** Diff `0020f3e..HEAD` confirms changes are limited to Synthesis §0 and §3.9. No research conclusions, rankings, or technology assessments were changed.

### 3.4 No direct Finance Suite runtime inspection

**Gap:** All four research reports describe external systems. None inspected the Finance Suite runtime (local Claude Code process, Engram, Memory, CC/C agent communication, or production deployment).

**Implication:** Any claim about what the Finance Suite runtime "does" or "requires" that is sourced from these reports is at most a hypothesis. Future windows that intend to make substrate-level claims must first collect runtime evidence.

**Next action:** Before any architecture decision, open a `Runtime Evidence Collection` window that inspects the actual Finance Suite substrate and maps findings to the external patterns documented in the four reports.

---

## 4. Next verification requirements

### 4.1 Immediate (this window)

| # | Action | Owner | Status |
|---|---|---|---|
| 1 | Downgrade Synthesis §0 and §3.9 overstatements | CC | ✅ Done (this remediation) |
| 2 | Update Research status to "Evidence Remediation Required" | CC | ✅ Done |
| 3 | Create this remediation plan | CC | ✅ Done |
| 4 | Commit with freeze-status message | CC | Pending |

### 4.2 Short-term (next authorized window)

| # | Action | Owner | Depends on |
|---|---|---|---|
| 5 | Review and commit `SOURCE_MATRIX.md` | CC | #4 |
| 6 | Verify capability verdict column per candidate | CC | #5 |
| 7 | C independent re-review of Synthesis §0/§3.9 changes | C | #4 |
| 8 | C independent re-review of Source Matrix | C | #5 |

### 4.3 Medium-term (future window, requires new authorization)

| # | Action | Owner | Depends on |
|---|---|---|---|
| 9 | Runtime Evidence Collection — inspect Finance Suite substrate directly | CC + C | #7, #8 |
| 10 | Map collected runtime evidence to external research patterns | CC | #9 |
| 11 | Architecture decision: process / substrate / scope-narrowing / combination | Human principal `Zhuanz` | #10 |

---

## 5. Boundary declaration

This remediation plan affirms the boundary that was present in the original research outputs but was weakened by the Synthesis overstatements:

```
REFERENCE ONLY
NOT ADOPTED
NOT ARCHITECTURE DECISION
NOT IMPLEMENTATION AUTHORIZATION
CAPABILITY NOT PROVEN
```

The research Phase 1 outputs are external reference material. They describe patterns observed in other systems. They do **not**:

- Inspect the Finance Suite runtime
- Prove that Finance Suite requires a substrate-level harness
- Prove that procedure alone is insufficient
- Authorize any architecture decision, adoption, or implementation

---

## 6. Cross-references

- `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` — original task card (status updated)
- `docs/research/ORG_LEVEL_AGENT_HARNESS_SYNTHESIS_v0.1.md` — synthesis (overstatements downgraded)
- `docs/research/ORG_LEVEL_AGENT_HARNESS_PHASE1_CLOSURE_REVIEW.md` — closure review (PASS WITH CONDITIONS)
- `docs/research/C_PHASE1_METHOD_NOTE_v0.1.md` — C's Phase 1 constraints
- `docs/research/ORG_LEVEL_HARNESS_SOURCE_MATRIX_v0.1.md` — untracked, pending review
- `docs/research/ORG_LEVEL_HARNESS_INDUSTRY_REPORT_v0.1.md` — Agent A
- `docs/research/ORG_LEVEL_HARNESS_OPEN_SOURCE_REPORT_v0.1.md` — Agent B
- `docs/research/ORG_LEVEL_HARNESS_GOVERNANCE_REPORT_v0.1.md` — Agent C
- `docs/research/ORG_LEVEL_HARNESS_SOFTWARE_PRACTICE_REPORT_v0.1.md` — Agent D

---

**End of remediation plan**
