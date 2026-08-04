# C Independent Verification Setup v0.1

**Status:** OPEN — reviewer environment not yet independently established
**Date:** 2026-08-04
**Trigger:** C returned BLOCKED on RRA Closure Plan Re-review — input files and git objects were not accessible in C's workspace
**Production:** UNCHANGED
**Implementation:** NOT AUTHORIZED
**Push:** FORBIDDEN

---

## 1. Why this exists

C's re-review of `RRA_v0.1_CLOSURE_PLAN.md` returned **BLOCKED**. The reason was not a content defect — it was that C's workspace did not contain the review inputs and could not resolve the git objects referenced in the review brief.

This exposed a structural gap in the review process:

```
Previously (invalid):
  CC writes documents
      ↓
  CC simulates C in same session/worktree/git-db
      ↓
  "PASS"
      ↓
  Producer Self Review — NOT independent

Required (valid):
  CC writes documents
      ↓
  C opens independent workspace
      ↓
  C verifies: files accessible, git objects resolvable
      ↓
  C performs review against primary evidence
      ↓
  Independent verdict
```

This setup document establishes the minimum conditions C's workspace must satisfy before any review can be considered independent.

---

## 2. Reviewer workspace

C must operate from a workspace that has access to the finance-suite repository.

**Option A — Same machine, same clone:**

```
Workspace: /Users/Zhuanz/finance-suite
Risk:     shared worktree with CC; untracked directories and uncommitted
          modifications may leak into C's view
```

**Option B — Separate clone:**

```
Workspace: /Users/Zhuanz/finance-suite-review  (or equivalent)
Setup:    git clone https://github.com/jinny280401-glitch/finance-suite.git
          git fetch origin
```

The workspace choice must be recorded in C's review output (§Review Environment Verification).

---

## 3. Required inputs

C must confirm each of the following is accessible before beginning review:

| Input | Path | SHA (if committed) |
|---|---|---|
| RRA Closure Plan | `docs/reviews/RRA_v0.1_CLOSURE_PLAN.md` | `b5428cd` |
| RRA Adversarial Review | `docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md` | `5ddb7ec` |
| RRA Assessment | `docs/reviews/RELEASE_READINESS_ASSESSMENT_v0.1.md` | `a75aac6` |
| Baseline Freeze Declaration | `docs/reviews/BASELINE_FREEZE_DECLARATION_v0.1.md` | (multiple revisions) |

---

## 4. Git object verification

Before reviewing content, C must independently verify:

```
git rev-parse 12649ca    → must resolve
git rev-parse 1ea582f    → must resolve (current HEAD at time of C's BLOCKED)
git rev-parse b5428cd     → must resolve (Closure Plan v0.2)
git rev-parse 5ddb7ec     → must resolve (Adversarial Review)
git rev-parse a75aac6     → must resolve (Assessment)
```

If any SHA does not resolve, C must report which and BLOCK the review.

If C is working from a separate clone that does not contain these local-branch commits, CC must push the `runtime-validation-v0.1` branch to a remote C can fetch, or C must be directed to the correct local repository path.

---

## 5. Required review output section

Every future C review artifact must begin with:

```markdown
## Review Environment Verification
Reviewer workspace:     <absolute path>
Repository:             <path or remote URL>
Branch/HEAD:            <ref>
Baseline SHA resolvable: <12649ca — YES/NO>
Input files accessible:  <count>/<total>
Git objects verified:    <list of SHAs and resolution status>
```

If any of these checks fail, the review MUST return BLOCKED before proceeding to content review.

---

## 6. Post-setup state

After C confirms the verification environment:

- Re-issue the C re-review task card with confirmed file paths and resolvable SHAs.
- C performs the review against primary evidence (not CC's conclusions).
- The review output carries the §Review Environment Verification section.

Until then:

```
RRA v0.1
  Baseline:                  12649ca
  Assessment:                COMPLETE
  Closure Plan:              CONTRACT COMPLETE
  Independent Verification:  BLOCKED
    Reason:                  Reviewer workspace not independently established
  Implementation:            NOT AUTHORIZED
  Push:                      FORBIDDEN
```

---

## 7. Cross-references

- `docs/reviews/RRA_v0.1_CLOSURE_PLAN.md`
- `docs/reviews/RRA_CLOSURE_PLAN_ADVERSARIAL_REVIEW_v0.1.md` (C's BLOCKED review)
- `docs/reviews/RELEASE_READINESS_ASSESSMENT_v0.1.md`
- `docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md`
- `docs/reviews/BASELINE_FREEZE_DECLARATION_v0.1.md`

---

**End of setup**
