# C Task Card — Baseline Integrity Review v0.1

**Role:** Independent Evidence Reviewer
**Mode:** READ-ONLY — output as reply body, do not modify any file
**Window:** Pre-Release-Readiness gate
**Author of card:** CC

---

## Why this card exists

Repository Handoff Cleanup v0.1 closed at commit `987fe8b`. Local HEAD has since moved to `5f876cf`. The window boundary of the previous window is intact (push forbidden, remote unchanged) but the candidate input for any future window is now ambiguous. This card exists to resolve that ambiguity before any subsequent window opens.

---

## Required baseline (do not modify)

```
Repository:        ~/finance-suite
Remote canonical:  origin/main  (= cefc660 = v0.1-main-consolidation)
Previous close:    987fe8b
Current HEAD:      5f876cf
Delta:             +1 commit
```

Both `987fe8b` and `5f876cf` are local-only commits; neither is on `origin/main`. No push has occurred. Do not push, do not fetch, do not reset, do not cherry-pick during this review.

---

## Attestation requirement

Every claim in the review must be backed by direct evidence and include `observed_at`. The card author CC has just written five boundary rules (`docs/governance/REPOSITORY_BOUNDARY_RULES_v0.1.md`, rules A–E); this review is the first place those rules are operationalized as the auditor's contract, not the auditor's target.

Specifically:

- For file content: read the file directly. Quote the line range.
- For commit content: `git show <sha> --stat` and `git show <sha> -- <path>` as needed.
- For commit metadata: `git show --no-patch --format=...` only.
- For repo state: `git status`, `git log --oneline -3`, `git ls-tree -r --name-only`, with `observed_at`.

Rule A (evidence type matches asset type) applies. Rule B (temporal validity) applies. Rule C (claim strength) applies. Rule D (workspace inventory snapshot) does not apply unless C observes untracked changes during the review — if observed, report as a finding, do not act.

---

## Scope

Compare `987fe8b` vs `5f876cf`. Only the differences.

For each file touched by `5f876cf`, output:

```
File:
Diff size:          lines added / removed
Type:               governance doc | review artifact | production code
                    | deployment asset | runtime code | other
Claim change:       what claim (if any) is altered, removed, or added
Boundary impact:    does this change Repository Boundary v0.1?
                    does it change REPOSITORY_BOUNDARY_RULES_v0.1?
                    does it change any R-01/R-02/R-03 status?
RRA input:          does this file belong in Release Readiness
                    Assessment v0.1 scope, or is it a different track?
Evidence:           specific diff hunks, line refs
```

---

## Required questions (answer each, with evidence)

1. **What does `5f876cf` change?**
   List the files and the semantic class of each change.

2. **Does `5f876cf` contain any of the following?**
   - production code change
   - runtime behavior change
   - deployment change
   - credential exposure
   - boundary rule modification
   - evidence of an already-merged remediation

3. **Does `5f876cf` alter the previously closed Repository Handoff Cleanup v0.1 verdict?**
   Specifically: does it change the BLOCKING/MAJOR findings, the capability verdict (`NOT PROVEN`), or the untracked directory classification? YES / NO per item, with evidence.

4. **Is `5f876cf` acceptable as the input baseline for Release Readiness Assessment v0.1?**
   - `ACCEPT AS INPUT` — C recommends proceeding with RRA based on `5f876cf`
   - `HOLD BASELINE` — C recommends not proceeding; the new commit either changes scope, requires human review, or is itself unevidenced

---

## Out of scope

- Do not review R-01 / R-02 / R-03 remediation content itself. That track is separate and is not in the path of this gate.
- Do not propose fixes to anything in `5f876cf`.
- Do not open Release Readiness Assessment v0.1.
- Do not write `MAIN_RELEASE_MANIFEST` or any other RRA artifact.
- Do not cherry-pick, merge, reset, or push.

---

## Constraints

```
❌ No file modification
❌ No commits
❌ No pushes
❌ No merge / cherry-pick / reset
❌ No new RRA artifacts
✅ Read-only diff inspection
✅ Output is reply body only
```

---

## Acceptance criteria

```
Previous-close SHA verified:     987fe8b
Current HEAD verified:           5f876cf
observed_at:                    stated in reply header
File diff enumerated:           all files in 5f876cf
Required questions answered:    4/4
Verdict:                        ACCEPT AS INPUT | HOLD BASELINE
File modification:              NONE
```

---

## CC pre-flight verification (already performed at card-write time)

```
[1] git rev-parse HEAD                  -> 5f876cfa6990c12774c92730d7aec77ad28570d3  ✓
[2] git log --oneline 987fe8b..HEAD     -> 1 commit                                   ✓
[3] subject                             -> matches expected                          ✓
[4] git show 5f876cf --stat             -> 1 file: RUNTIME_REMEDIATION_PLAN_v0.1.md  ✓
                                          (+122 / -32)
[5] tree diff (sorted)                  -> only RUNTIME_REMEDIATION_PLAN_v0.1.md    ✓
                                          (987fe8b: 214 paths; 5f876cf: 214 paths)
[6] git status                          -> 4 untracked dirs, ahead of origin/main   ✓
```

The card is written. CC awaits C's reply before any further action.
