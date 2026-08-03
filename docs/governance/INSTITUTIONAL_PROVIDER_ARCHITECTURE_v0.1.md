# Institutional Evidence Provider Architecture v0.1

**Status:** DESIGN / NORMATIVE DRAFT
**Effective date:** 2026-07-29
**Scope:** All institutional evidence provider adapters in Finance Suite
**Runtime implementation:** NOT ESTABLISHED
**Production capability:** NOT CLAIMED
**Design reference:** Gildata Studio / 聚源 Studio (design template only, not implementation proof)

## 1. Purpose

Define a unified Provider Adapter architecture standard so that Wind, Choice, iFinD, Tushare, Gildata and other institutional evidence sources can be onboarded under the same capability and evidence semantics.

This document is a normative governance spec. It governs how a provider may be claimed, not whether any provider is already wired.

## 2. Provider Adapter Lifecycle

```text
Credential
  -> Transport
  -> Session
  -> Evidence Retrieval
  -> Normalization
  -> Evidence Manifest
  -> QC Integration
  -> Runtime Consumer
  -> Capability Claim
```

The lifecycle is sequential. A later stage MUST NOT be claimed before every earlier required stage is proven.

## 3. Capability State Machine

```text
UNKNOWN
CREDENTIAL_EXISTS
CREDENTIAL_LOADED
TRANSPORT_VERIFIED
SESSION_ESTABLISHED
EVIDENCE_RETRIEVED
NORMALIZED
MANIFEST_BOUND
QC_INTEGRATED
CONSUMER_PROVEN
PRODUCTION_CAPABLE
```

### 3.1 Ordering rationale

- `CREDENTIAL_EXISTS` — provider credential artifact exists at a known path.
- `CREDENTIAL_LOADED` — credential successfully loaded into runtime context.
- `TRANSPORT_VERIFIED` — connection to the provider endpoint is reachable and the protocol layer responds as designed.
- `SESSION_ESTABLISHED` — authenticated session with the provider is opened and bound to a principal class.

Transport is a connection-layer fact. Session is an authenticated state. The capability to retrieve evidence depends on Session, not on Transport alone.

### 3.2 Mandatory invariants

```text
CREDENTIAL_EXISTS      != CREDENTIAL_LOADED
CREDENTIAL_LOADED      != TRANSPORT_VERIFIED
TRANSPORT_VERIFIED     != SESSION_ESTABLISHED
SESSION_ESTABLISHED    != EVIDENCE_RETRIEVED
EVIDENCE_RETRIEVED     != NORMALIZED
NORMALIZED             != MANIFEST_BOUND
MANIFEST_BOUND         != QC_INTEGRATED
QC_INTEGRATED          != CONSUMER_PROVEN
CONSUMER_PROVEN        != PRODUCTION_CAPABLE
```

A provider MUST NOT skip a state. Each promotion requires evidence produced at that stage.

## 4. Provider Interface Contract (Normative)

A conformant provider adapter MUST expose the following components. Names are illustrative; equivalent implementations are acceptable if they satisfy the contract.

```text
ProviderIdentity
  name, version, environment

CredentialLoader
  load() -> LoadedCredential | LoadFailure
  return: success receipt only, NEVER secret material

TransportAdapter
  connect() / disconnect() / healthcheck()
  return: TransportEvidence (reachability, protocol semantics)

SessionManager
  open(principal_class) -> Session | SessionFailure
  return: session_id, expiry, principal_class_redacted
  close(session_id)

EvidenceRetriever
  query(scope, session) -> RawEvidence + SessionContext
  return: raw_response, raw_response_sha256, request_id, timestamps

Normalizer
  normalize(raw, schema_version) -> NormalizedEvidence
  return: field_mapping_verified, normalized_sha256

EvidenceManifestBuilder
  build(normalized, provenance) -> Manifest
  MUST conform to Vera Evidence Manifest Protocol v0.1

QCIntegrator
  integrate(manifest, qc_policy) -> QCAnnotatedManifest
  return: qc_status, allowed_use, blocked_fields, confidence_boundary

ConsumerHook
  consume(qc_manifest) -> ConsumerResult + Receipt
  return: end-to-end PASS / PARTIAL / FAIL / UNKNOWN

CapabilityLicense
  bind(verdict, evidence, governance) -> License | Rejection
  MUST conform to Vera Capability Claim Governance Framework v1
```

## 5. Required Evidence per Stage

| Stage | Required evidence | Must NOT contain |
|---|---|---|
| `CREDENTIAL_EXISTS` | file path, format metadata, existence timestamp | secret content |
| `CREDENTIAL_LOADED` | load success receipt, loader identity | plaintext credential, token, cookie |
| `TRANSPORT_VERIFIED` | reachability log, protocol observation, transport fingerprint | credentials |
| `SESSION_ESTABLISHED` | session_id, expiry, principal class (redacted), issuer | session token |
| `EVIDENCE_RETRIEVED` | request_id, raw_response_sha256, retrieved_at, source_timestamp | raw body if secrets may be present |
| `NORMALIZED` | normalized_sha256, field_mapping_verified, schema_version | raw provider payloads |
| `MANIFEST_BOUND` | manifest_id, manifest_sha256, mapping_verified | secrets, cookies, bearer tokens |
| `QC_INTEGRATED` | qc_status, allowed_use, blocked_fields, confidence_boundary, decision_reason | sensitive runtime internals |
| `CONSUMER_PROVEN` | end-to-end receipt PASS/PARTIAL/FAIL/UNKNOWN, verifier, verified_at | session cookies, passwords |
| `PRODUCTION_CAPABLE` | unexpired, unrevoked, valid Capability License (issuer, issued_at, expires_at, revoke_conditions) | secrets |

## 6. Provider Catalog (Future Reference, NOT Implemented)

| Provider | Adapter | State |
|---|---|---|
| Gildata Studio / 聚源 Studio | GildataStudioAdapter | PENDING — v0.1 design reference only |
| Wind | WindAdapter | PENDING |
| Choice / EmQuantAPI | ChoiceAdapter | PENDING |
| iFinD / THS | iFinDAdapter | PENDING |
| Tushare Pro | TushareAdapter | PENDING |

No provider in this catalog is integrated, verified, or production-capable as of v0.1.

## 7. Failure and Downgrade Rules

- Any stage failure MUST downgrade the provider to the highest still-proven lower state.
- Hash mismatch, mapping failure, expiry, revocation, missing required evidence MUST fail closed.
- Multi-source fallback MUST NOT be collapsed into a single-source capability claim.
- A downstream consumer failure MUST NOT retroactively invalidate upstream provider evidence.
- Provider drift (schema, endpoint, contract) MUST reset state to the lowest affected verified level.

## 8. Anti-Patterns (Explicitly Forbidden)

- Using ping or endpoint reachability to prove business capability.
- Treating a sandbox or mock test as production evidence.
- Describing an API call success as "integrated".
- Generalizing one provider's verified state to the whole catalog.
- Collapsing multi-source fallback results into a single-source claim.
- `Credential Exists != Provider Capability Proven`.
- `Smoke Test PASS != Production Capability PASS`.

## 9. Compatibility with Existing Governance

This architecture aligns with:

- `Vera_Capability_Claim_Governance_Framework_v1` — capability maturity ladder and `LIVE VERIFIED` license model.
- `Vera_Evidence_Manifest_Protocol_v0.1` — three-question audit linkage.
- Existing Evidence Manifest Contract v0 — sanitized evidence objects consumed by sections.

A provider MUST NOT promote itself above `TRANSPORT VERIFIED` without producing a manifest conforming to the Protocol, and MUST NOT claim `LIVE VERIFIED` without a valid Capability License from the Framework.

## 10. Out of Scope (v0.1)

- Multi-provider merge and conflict resolution semantics.
- Cross-provider data consistency verification.
- Cost, quota, billing governance (handled by independent `provider_policy` module).
- Provider-specific feature catalogs.
- Implementation detail of any single adapter (Gildata Studio or otherwise).