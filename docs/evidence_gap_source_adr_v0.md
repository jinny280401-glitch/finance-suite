# ADR: Evidence Gap Source Must Be Explicitly Recorded

**Status**: Accepted  
**Date**: 2026-06-11  
**Scope**: Supply Chain Consistency Discovery / Gate A-2 governance  

## Context

Gate A-2 produced a repeatable ambiguity: a case may pass while still containing an evidence gap.

If the gap is recorded only as `PASS WITH EVIDENCE GAP`, reviewers cannot tell whether the issue is a missing structure or reduced evidence quality.

Those are different risks:

- Missing structure can block method validation.
- Reduced evidence quality can lower confidence without invalidating method validation.

## Decision

Evidence Gap is not a verdict.

Evidence Gap is a classified finding.

Any case marked as `PASS WITH EVIDENCE GAP` must explicitly record:

- Gap Type
- Gap Severity
- Gap Impact

The team must classify the source of the gap, not merely report that a gap exists.

## Taxonomy v0

### Type A: Structural Gap

Examples:

- Missing Field
- Missing Rule
- Missing Traceability
- Missing Time Series

Characteristics:

- Blocks `Field -> Rule -> Verdict`
- Blocks Method Validation

Example:

```text
installation missing
```

Result:

```text
Method Validation = BLOCKED
```

### Type B: Quality Gap

Examples:

- Field Hierarchy Mismatch
- Evidence Quality Mismatch
- Coverage Mismatch
- Market-Level vs Company-Level Mismatch

Characteristics:

- `Field -> Rule -> Verdict` exists
- Method Validation remains possible
- Confidence is reduced

Example:

```text
installation = market / regional level
shipment     = company level
inventory    = company level
```

Result:

```text
Rule Supported      = YES
Causal Chain Proven = NO
```

## Required Recording Fields

Every Evidence Gap must include:

| Field | Requirement |
| --- | --- |
| Gap Type | Structural Gap or Quality Gap |
| Description | Plain-language gap explanation |
| Impact Scope | Which field, rule, verdict, or causal link is affected |
| Blocks Method Validation | Yes / No |
| Confidence Penalty | None / Low / Medium / High |
| Mitigation Path | What evidence or field would reduce or close the gap |

## Governance Rule

A case may pass while still containing Evidence Gaps.

Therefore every Evidence Gap must be classified, not merely reported.

Structural Gaps block Method Validation.

Quality Gaps reduce confidence but do not necessarily invalidate Method Validation.

## Session 1 Reference Case

Task #19 demonstrates the transition from a Structural Gap to a Quality Gap.

Before Task #19:

```text
installation missing
  -> Structural Gap
  -> Method Validation Blocked
```

After Task #19:

```text
installation exists
  -> Quality Gap
  -> Method Validation Allowed
  -> PASS WITH EVIDENCE GAP
```

The remaining Paine risk is no longer `Missing Field`.

The remaining risk is `Field Hierarchy Mismatch`:

```text
installation = market / regional level
shipment     = company level
inventory    = company level
```

This means:

```text
Field Exists ........ YES
Rule Exists ......... YES
Verdict Exists ...... YES
Rule Supported ...... YES
Causal Chain Proven . NO
```

## Consequences

Gate A-2 produced two governance assets:

1. Method Candidate
2. Evidence Gap Taxonomy

The second asset may be more durable than the first.

`Method Candidate` may be revised, upgraded, or rejected by future sessions.

`Evidence Gap Taxonomy` should apply to every future case review because it separates method failure from evidence-quality degradation.
