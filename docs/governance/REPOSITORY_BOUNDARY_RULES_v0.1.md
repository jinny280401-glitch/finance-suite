# REPOSITORY_BOUNDARY_RULES_v0.1

**Status:** DRAFT (first formalization; produced from Repository Handoff Cleanup v0.1)
**Effective from:** 2026-08-04
**Source window:** Repository Handoff Cleanup v0.1
**Scope:** All repository evidence used in audit, governance, and capability claims
**Supersedes:** None
**Aligns with:** `EVIDENCE_GOVERNANCE_v1.0.md`, `Vera_Capability_Claim_Governance_Framework_v1.md`

---

## Purpose

The five rules below were each triggered by a real failure during Repository Handoff Cleanup v0.1. They are written narrowly enough to be enforceable and broadly enough to apply beyond the incidents that produced them.

Each rule specifies:

- **Trigger** — the concrete event that exposed the gap
- **Rule** — the normative statement
- **Applies to** — asset types or activities bound by the rule
- **Anti-pattern** — what the rule forbids
- **Evidence format** — the minimum required fields on a conforming claim

---

## Rule A — Evidence Object Type Must Match Asset Type

**Trigger:** First-send C task card required a commit-level attestation for untracked workspace directories. C correctly BLOCKED. The mistake was conflating two distinct evidence domains.

**Rule:** A claim about an asset MUST be backed by evidence from the asset's actual location:

| Asset type | Required evidence |
|---|---|
| Committed (in any reachable commit) | `git ls-tree -r <sha> --name-only` plus the SHA itself |
| Untracked (in working tree only) | `ls -la <path>` plus the path and `observed_at` |
| File content (either committed or untracked) | direct `Read` of the file with path and `observed_at` |
| Runtime (production or staging) | server-side observation; not in scope of this repository's evidence |

A claim MAY cross types only when the chain of evidence is itself recorded (e.g. "this untracked path is the working-tree version of a path that exists at commit X with hash Y" — and that equivalence must be stated explicitly).

**Applies to:** all audit reports, capability claims, drift reports, and handoff documents produced for the finance-suite repository.

**Anti-pattern:** Requiring a `commit SHA` attestation for an asset that does not exist in any commit. The reverse is also forbidden: claiming a `cefc660` property for a file that is not in the `cefc660` tree.

**Minimum evidence fields on a conforming claim:**

```
asset_path:    absolute or repo-relative path
asset_state:   committed | untracked | both
observed_at:   ISO-8601 timestamp
evidence:      the specific command or read used
```

---

## Rule B — Temporal Validity of Repository Evidence

**Trigger:** During P0.3 of this window, an early read of `git rev-list --left-right --count origin/main...HEAD` for `codex/sidebar-market-temperature-fallback` returned `ahead 1, behind 6`. A re-read minutes later returned `0 5`. The numbers changed because `origin/main` advanced between reads, not because the local branch moved. The original ahead/behind values were presented as if they were stable facts and would have been misleading if not re-checked.

**Rule:** Repository evidence with non-trivial time dependence MUST carry the snapshot context under which it was obtained. A claim about Git topology, workspace state, or any other time-varying property of the repository is valid only for the moment it was observed.

**Applies to:** all of the following, and any future category of repository evidence with similar shape:

- Git branch ahead/behind counts
- Working-tree untracked file list
- Working-tree modified file list
- Runtime endpoint reachability (out of scope but referenced)
- Any external service state observable from the repository's vantage

**Anti-pattern:** Citing `behind 5` or `4 untracked dirs` in a document without `observed_at` and without the reference SHA(s) used to compute it. Reading a value once, writing it down, and treating the written form as durable.

**Minimum evidence fields on a conforming claim:**

```
observed_at:       ISO-8601 timestamp
reference_sha:     the SHA the claim was computed against (e.g. origin/main SHA)
local_sha:         the local SHA used (if applicable)
scope:             what was included / excluded
```

---

## Rule C — Claim Strength Must Match Evidence Strength

**Trigger:** README in `cefc660` references `deploy-backend.sh` four times, and the file exists at the repository root. C observed that the README does not document what `deploy-backend.sh` deploys. Independently, the `deploy.sh` script that runs in production does not invoke `deploy-backend.sh` and does not deploy any backend artifact. The presence of the script and the four README references are real; the inference "backend can be started" is not.

**Rule:** A claim of the form "X exists" does NOT imply "X works." Specifically, for the finance-suite repository, the following non-implications are normative:

| Evidence | Does NOT imply |
|---|---|
| `deploy-backend.sh` exists in the repo root | backend deployment works |
| `README.md` exists at the root | Local Reproduction succeeds |
| `scripts/auction_data.py` exists in `cefc660` | Auction P0 capability is available |
| `mcp_server.py` imports `auction_data` | MCP `/market_pulse` works in production |
| `server_scripts/intel_api.py` imports `market_context` | `/api/intel/market-context` works |
| `docs/architecture/...md` exists | the architecture is implemented |
| `docs/incidents/...md` exists | the underlying issue is resolved |
| `docs/signal-validation-v0.1/...md` exists | a signal is validated for production use |

**Applies to:** every capability claim, marketing claim, and handoff statement that touches the repository.

**Anti-pattern:** Collapsing "presence of artifact" into "capability proven." This includes: jumping from "fix exists" to "issue resolved" (the canonical anti-pattern from `INCIDENT_RCA_CARD_AUCTION_20260730.md`), from "tests pass" to "production proven," and from "documentation written" to "system understood."

**Minimum evidence fields on a conforming claim:**

```
claim:           the statement being made
evidence:        the artifact(s) supporting the claim
evidence_type:   existence | execution | measurement | external attestation
gap:             the steps between evidence_type and the claim being made
```

If `gap` is non-empty, the claim is at most `EVIDENCE_VERIFIED` per `Vera_Capability_Claim_Governance_Framework_v1.md` §3; it is not `LIVE_VERIFIED`.

---

## Rule D — Workspace Inventory Snapshot

**Trigger:** `aws-idea-to-frontier/` was excluded from `cefc660` during canonical main reconstruction (2026-08-03). It reappeared in the working tree on 2026-08-04 13:13. CC's review flow did not catch this reappearance in the moment — it was only detected because C read the file mtime and reported it. Without a recorded start-of-session inventory, CC had no basis to detect an addition during the session.

**Rule:** Every audit session that touches the working tree MUST begin by recording a workspace inventory snapshot. The end-of-session snapshot is compared to the start. Differences are attributed to: (a) the auditor's own actions, (b) external automation, or (c) a third party. Unattributed differences invalidate the audit.

**Applies to:** all audit windows, handoff cleanups, governance reviews, and any other session that asserts a property of the repository's working tree.

**Anti-pattern:** Starting a session that surveys "what is in the repo" without first recording "what was in the repo when I started." Conflating "what I have not touched" with "what has not changed."

**Minimum evidence fields on a conforming audit session:**

```
session_id:           unique identifier for the audit session
workspace_root:      absolute path
observed_at_start:   ISO-8601 timestamp
observed_at_end:     ISO-8601 timestamp
tracked_paths:       count + source command (e.g. git ls-tree -r <sha>)
untracked_dirs:      list with mtime
excluded_paths:      list per .gitignore
mid_session_changes: any path added/removed with attribution
```

---

## Rule E — Independent Review Must Surface the Auditor's Errors

**Trigger:** C's first review reported "README contains no `backend/` tree entry" as a fact. The literal claim was wrong (README references `deploy-backend.sh` four times and the file exists at the root). The underlying drift was real but different from what C described. CC caught the error only by reading the README directly while reconciling. If the report had been accepted verbatim, the fix would have targeted the wrong file.

**Rule:** An independent review's primary value is not agreement but **calibration of the auditor's claims**. A review that returns only "PASS" or only "confirmed" without surfacing even a single correction is, in this governance regime, evidence that the review was not independent enough. The Final Report and any future review artifact MUST record both the agreed findings AND the corrections.

**Applies to:** all independent reviews of CC-produced audit artifacts, and symmetrically all CC reviews of C-produced artifacts (in the language of this window: this is the two-agent review loop that produced the v0.1 Validation Report corrections and the present corrections).

**Anti-pattern:** "Review confirms the auditor's findings" with no corrections, no claimed-strength adjustments, and no claim-wording refinements. A pure-agreement review is treated as `UNKNOWN` for the purposes of the Capability Claim ladder until a substantive correction is documented at least once per window.

**Minimum evidence fields on a conforming review:**

```
reviewer:            identifier (C, CC, external)
reviewed_artifact:   path + commit SHA of the artifact under review
agreed_findings:     list of finding IDs the reviewer confirms
corrected_findings:  list of finding IDs the reviewer adjusts, with the correction
new_findings:        list of finding IDs the reviewer introduces
verdict:             PASS | PASS WITH CONDITIONS | UNKNOWN | BLOCKED (per scope)
```

---

## Cross-references

- `docs/governance/EVIDENCE_GOVERNANCE_v1.0.md` — provides the Evidence Object schema and the eight governing principles (Data present ≠ Evidence valid, etc.). Rules A–D operationalize Principle 7 (Declared Capability ≠ Effective Capability) for repository evidence.
- `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md` — the L0–L6 capability maturity ladder. Rule C maps the gap between `evidence_type` and `claim` onto the ladder: presence of evidence is at most L1 (SHELL VERIFIED) until execution and measurement are independently observed.
- `docs/reviews/REPOSITORY_HANDOFF_FINAL_REPORT_v0.1.md` — the audit that triggered this rule set.
- `docs/security/CREDENTIAL_EXPOSURE_TUSHARE_v0.1.md` — a Rule C violation that was caught during P0 of the same window.
- `docs/reviews/BRANCH_TRACKING_AUDIT_v0.1.md` — an instance of Rule B application.
- `docs/reviews/C_REPOSITORY_HANDOFF_REVIEW_BRIEF_v0.1.md` — the artifact that surfaced the need for Rule A.

---

## Change log

| Version | Date | Author | Note |
|---|---|---|---|
| v0.1 | 2026-08-04 | CC | First formalization. 5 rules. Each rule has a recorded trigger from this window. |
