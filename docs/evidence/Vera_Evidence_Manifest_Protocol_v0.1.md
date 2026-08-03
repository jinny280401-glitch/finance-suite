# Vera Evidence Manifest Protocol v0.1

**Status:** PROTOCOL DRAFT / NORMATIVE DESIGN
**Effective date:** 2026-07-29
**Runtime implementation:** NOT ESTABLISHED
**Production capability:** NOT CLAIMED

## 1. Purpose

The Vera Evidence Manifest Protocol is an internal audit protocol for linking what Vera observed, what Vera was allowed to say, and what reached the user.

It is not limited to a page or test harness. Intended profiles include:

- Provider Capability Manifest
- Company Evidence Manifest
- Market Evidence Manifest
- Morning Brief Manifest
- Close Brief Manifest
- Research Evidence Manifest
- Agent Output Manifest

The protocol does not itself verify evidence or issue `LIVE VERIFIED`. It records the material required by Truth Guard and the [Capability Claim Governance Framework](../governance/Vera_Capability_Claim_Governance_Framework_v1.md) to make those decisions.

## 2. Three Questions

### What did Vera see?

- source
- provider
- source timestamp
- retrieval timestamp
- request ID
- case ID
- raw response hash

### What was Vera allowed to say?

- QC status
- allowed use
- blocked fields
- confidence boundary
- Trust Gate decision and reason

### What exactly reached the user?

- artifact identity and link
- render hash
- raw-to-render mapping status
- delivery timestamp and channel

## 3. Protocol Position

```text
Provider Layer
  -> Raw Observation
  -> Research Runtime
  -> Trust Gate
  -> Evidence Manifest
  -> Presentation / Delivery
  -> User
```

Provider payloads MUST NOT be exposed to consumers merely because the manifest records their hash. Existing Evidence Contract rules that strip forbidden raw fields remain in force.

## 4. Canonical Manifest

```json
{
  "protocol": "vera-evidence-manifest",
  "manifest_version": "0.1",
  "manifest_id": "manifest:<uuid>",
  "profile": "provider|company|market|morning_brief|close_brief|research|agent_output",
  "capability_id": "",
  "environment": "local|staging|production",
  "case_id": "",
  "request": {
    "request_id": "",
    "requested_at": "",
    "authenticated": false,
    "principal_class": "redacted-class-only"
  },
  "observation": {
    "source": "",
    "provider": "",
    "source_timestamp": "",
    "retrieved_at": "",
    "raw_response_sha256": "",
    "http_status": null,
    "business_success": null
  },
  "trust_decision": {
    "qc_status": "success|partial|failure|unknown",
    "decision": "allow|limit|block|unknown",
    "allowed_use": [],
    "blocked_fields": [],
    "confidence_boundary": "",
    "decision_reason": ""
  },
  "presentation": {
    "artifact_id": "",
    "artifact_link": "",
    "artifact_sha256": "",
    "render_sha256": "",
    "mapping_verified": false,
    "delivered_at": "",
    "channel": ""
  },
  "validity": {
    "verified_at": "",
    "expires_at": "",
    "status": "valid|expired|revoked|unknown"
  },
  "authority": {
    "issuer": "",
    "issued_at": "",
    "revoke_conditions": []
  },
  "verdict": "UNKNOWN|SHELL_VERIFIED|TRANSPORT_VERIFIED|AUTH_BOUNDARY_VERIFIED|RUNTIME_VERIFIED|EVIDENCE_VERIFIED|LIVE_VERIFIED"
}
```

Secrets, cookies, bearer tokens, passwords, personally identifying authentication material, and unredacted private payloads MUST NOT appear in a manifest.

## 5. Required Invariants

1. `manifest_id`, `request_id`, and `case_id` MUST be stable and unique within their scopes.
2. Hashes MUST use SHA-256 over canonical or archived byte artifacts; the canonicalization method MUST be declared when serialization can vary.
3. `mapping_verified=true` requires a reproducible link between the archived raw-response hash and the rendered artifact, not merely matching timestamps.
4. `authenticated=true` requires evidence from an approved authenticated execution. It MUST NOT be inferred from an unauthenticated `401` check.
5. `qc_status=success` MUST NOT erase `blocked_fields` or expand `allowed_use`.
6. `verdict=LIVE_VERIFIED` requires a valid, unexpired, non-revoked license conforming to the Capability Claim Governance Framework.
7. A missing required field MUST remain missing or `unknown`; it MUST NOT be synthesized.
8. A prose summary MUST NOT replace the primary archived artifacts referenced by hashes.
9. Deployment or source drift invalidates artifact-bound verification until re-verified.

## 6. Verification Receipt

Verification SHOULD produce a separate receipt so the manifest cannot self-approve:

```json
{
  "receipt_version": "0.1",
  "manifest_id": "manifest:<uuid>",
  "manifest_sha256": "",
  "verified_at": "",
  "verifier": "",
  "checks": {
    "raw_artifact_present": false,
    "raw_hash_matches": false,
    "trust_decision_present": false,
    "render_artifact_present": false,
    "render_hash_matches": false,
    "mapping_verified": false,
    "within_validity_window": false,
    "requested_use_allowed": false
  },
  "result": "PASS|PARTIAL|FAIL|UNKNOWN"
}
```

The issuer of a capability license SHOULD be organizationally or procedurally separate from the process that generated the underlying artifact.

## 7. Failure and Downgrade Rules

| Condition | Maximum permissible state |
|---|---|
| Only page or artifact exists | `SHELL VERIFIED` |
| Route reachable, response semantics unverified | `TRANSPORT VERIFIED` |
| Auth boundary proven, authenticated business path absent | `AUTH BOUNDARY VERIFIED` |
| Runtime executed, primary evidence incomplete | `RUNTIME VERIFIED` |
| Complete linked evidence, license absent or expired | `EVIDENCE VERIFIED` |
| Complete linked evidence and valid license | `LIVE VERIFIED` |

`UNKNOWN`, expiry, revocation, hash mismatch, or mapping failure MUST fail closed.

## 8. Demo Profile

A competition or recorded demonstration MAY use a Demo Manifest with:

- `environment=local` or a dedicated demo environment;
- immutable recorded or fixture artifacts;
- explicit capture timestamp and source;
- visible `DEMO MODE - RECORDED/TEST DATA - NOT LIVE` labeling;
- a maximum claim of `SHELL VERIFIED` or an explicitly separate `DEMO VERIFIED` presentation status.

A Demo Manifest MUST NOT authorize `LIVE VERIFIED`, Production Ready, or a production-data claim.

## 9. Compatibility

This protocol complements the existing `Evidence Manifest Contract v0`:

- the existing contract governs the sanitized evidence objects Sections may consume;
- this protocol governs end-to-end audit linkage across request, observation, Trust Gate decision, artifact, and capability claim.

The protocol MUST NOT reintroduce forbidden raw provider fields into LLM or Section context.
