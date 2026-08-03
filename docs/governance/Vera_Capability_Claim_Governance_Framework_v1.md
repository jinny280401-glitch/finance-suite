# Vera Capability Claim Governance Framework v1.0

**Status:** GOVERNANCE SSOT / NORMATIVE
**Effective date:** 2026-07-29
**Scope:** All Vera providers, runtimes, features, artifacts, presentations, and external capability claims

## 1. Purpose

Vera governs not only features, but claims about what those features can do.

> Truth Guard is a Capability Claim Firewall. It does not determine whether the world is absolutely true. It controls which capabilities Vera may claim at each evidence maturity level.

Examples of governed claims include:

- Vera has integrated Wind.
- Vera performs real-time market analysis.
- Vera automatically generates research reports.
- Vera supports institutional-grade research.

Every capability claim MUST be scoped and bound to evidence. Words such as `connected`, `supported`, `live`, `verified`, and `production-ready` MUST NOT be used as unqualified single-state conclusions.

## 2. Governing Principle

```text
Feature exists
    !=
Capability may be claimed
```

The allowed claim MUST NOT exceed the lowest verified maturity level of any component required by that claim.

Truth Guard therefore governs capability promotion:

```text
Input
  -> evidence maturity
  -> allowed-use boundary
  -> runtime execution
  -> user artifact
  -> capability claim
```

## 3. Capability Maturity Ladder

This ladder is the single source of truth for capability-claim status.

| Level | Status | Evidence required | Permitted claim |
|---:|---|---|---|
| 0 | `UNKNOWN` | No valid evidence | No capability claim |
| 1 | `SHELL VERIFIED` | Page, control, interaction, or presentation asset exists | Shell or prototype exists |
| 2 | `TRANSPORT VERIFIED` | Route is reachable and protocol behavior is observed | Transport path exists |
| 3 | `AUTH BOUNDARY VERIFIED` | Authentication boundary fails closed and behaves as designed | Authentication boundary exists |
| 4 | `RUNTIME VERIFIED` | A real scoped request executes through data acquisition, processing, and response | Runtime works in the verified scope |
| 5 | `EVIDENCE VERIFIED` | Input, trust decision, output, and provenance are reproducibly linked | Verified evidence supports the scoped capability |
| 6 | `LIVE VERIFIED` | A valid, unexpired Evidence Manifest license authorizes the live claim | Live capability may be claimed within license scope |

Each level is a constraint level, not a marketing grade. Higher levels require new evidence; they are never inferred from lower levels.

Critical invariant:

```text
AUTH BOUNDARY VERIFIED != AUTHENTICATED RUNTIME VERIFIED
```

An endpoint returning the correct unauthenticated `401` proves the boundary, not the authenticated business path.

## 4. Claim Evaluation Rule

Every claim MUST identify:

- `capability_id`
- environment
- required components
- maturity of each component
- controlling Evidence Manifest, if any
- permitted wording
- prohibited wording

The claim maturity is:

```text
claim_maturity = minimum(required_component_maturities)
```

If any required component is `UNKNOWN`, expired, drifted, revoked, or unlinked, the claim MUST fail closed to the highest still-proven lower state.

## 5. LIVE VERIFIED License

`LIVE VERIFIED` is not an ordinary UI status.

> LIVE VERIFIED is a scoped, time-bound, revocable capability license.

The license MUST bind:

```yaml
capability: capability identifier and exact scope
environment: target environment
manifest_version: Vera Evidence Manifest Protocol version
evidence:
  raw_response_hash: sha256
  render_hash: sha256
  mapping_verified: true
governance:
  allowed_use: []
  blocked_fields: []
validity:
  verified_at: ISO-8601
  expires_at: ISO-8601
authority:
  issuer: verifier identity
  revoke_conditions: []
```

A license MUST be downgraded or revoked when:

- it expires;
- source, provider, runtime, schema, prompt, deployment, or artifact identity drifts;
- required hashes no longer match;
- raw-to-output mapping cannot be reproduced;
- authentication or runtime verification fails;
- the requested use exceeds `allowed_use`;
- a listed revoke condition occurs.

Historical verification MUST NOT automatically authorize a current live claim.

## 6. Truth Guard Requirements

Truth Guard MUST:

- block evidence-level overstatement;
- distinguish shell, transport, authentication, runtime, evidence, and live states;
- expose `UNKNOWN`, missing, expired, and revoked states without silently promoting them;
- preserve `allowed_use` and `blocked_fields` through the user-facing artifact;
- default to the highest proven lower state when evidence is incomplete;
- keep Production Ready as a separate decision gate.

Truth Guard MUST NOT:

- convert HTTP success into business success;
- convert a UI render into runtime proof;
- convert authentication-boundary evidence into authenticated-runtime evidence;
- convert a historical demonstration into current live proof;
- treat a summary document as a substitute for missing primary evidence;
- claim absolute truth or that AI can never be wrong.

## 7. Required Claim Language

Preferred product statement:

> Vera does not try to make AI incapable of error. It changes how AI errors are allowed to enter business workflows.

Competition-safe statement:

> Vera does not claim that every piece of information is always correct. It ensures that unverified evidence is never presented as verified capability.

Chinese:

> Vera 不保证所有信息永远正确，但保证任何未经验证的信息，都不会被包装成已验证能力。

## 8. Relationship to Evidence Protocol

This framework decides **whether a capability claim is authorized**.

`Vera Evidence Manifest Protocol` supplies the audit credential used by that decision. An Evidence Manifest does not automatically issue `LIVE VERIFIED`; the manifest must be complete, valid, current, scoped to the requested use, and accepted by the appropriate authority.

## 9. Initial Governance Finding

The first canonical case is:

> A capability claim exceeded its evidence maturity level.

[`Presentation Truth Guard RCA 20260727`](../findings/Presentation_Truth_Guard_RCA_20260727.md) established that Presentation Shell, route presence, and authentication boundary could be proven while authenticated runtime evidence and durable raw-to-render provenance could not. Truth Guard correctly prevented promotion to Live Presentation.

This is a governance success with an Evidence Layer finding, not proof of production capability.
