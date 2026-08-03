# GO: Repository Share Remediation Plan

**Status:** PLAN DEFINED / EXECUTION NOT AUTHORIZED
**Created:** 2026-07-29
**Current gate:** Builder Onboarding BLOCKED
**Permission changes:** FROZEN; two existing `Depwater` write invitations remain pending

## Objective

Move the repository from `BLOCKED` toward a state that can independently prove `Builder Ready: YES`.

This is not a “fix Git” task. It is a staged evidence and repository-boundary remediation program.

This plan does not authorize:

- commit or push;
- collaborator or permission changes;
- invitation acceptance, expansion, or revocation;
- deletion;
- `.gitignore` modification;
- force push or history rewrite;
- secret value extraction or redistribution;
- Builder data handoff.

## P0: Secret Exposure Review

P0 is the first blocking gate because the GitHub repository is public.

### Scope

At minimum inspect:

- current and historical `DEPLOY_AUTH_FIX.md`;
- `docs/internal/reference_finance_suite_accounts.md`;
- `fix_auth_system.md`;
- other tracked or historical authentication/account material;
- ignored local `.env` and `.env.save`, recording only path, permissions, and classification evidence.

Secret values must never be copied into reports, chat, commits, or manifests.

### Classification

Every candidate must receive one classification:

| Class | Meaning | Required evidence |
|---|---|---|
| A | Real and potentially valid secret | Provider/issuer-side revocation or rotation evidence |
| B | Real but rotated or invalidated | Durable rotation/invalidity evidence |
| C | Test placeholder | Proof it cannot authenticate to a real system |
| D | Documentation example | Proof it is synthetic and does not expose a real account |
| UNKNOWN | Evidence insufficient | Remains a blocker |

A public-history candidate must be treated as exposed until classification evidence proves otherwise.

### P0 Pass

- every candidate classified;
- no UNKNOWN;
- all A material revoked or rotated;
- all B material has invalidity evidence;
- account, VIP, customer, and PII exposure has a public-safety decision;
- no active secret remains in the intended public baseline.

If history contains A or B material, history remediation requires a separate high-risk authorization after rotation. This plan does not authorize deletion or history rewriting.

## P1: Repository Boundary Classification

Do not solve the current 7 ahead commits, 17 tracked modifications, and 27 untracked entries by committing everything.

### Inventory Classes

- intended release source;
- governance source;
- generated deliverable;
- local runtime artifact;
- cache, log, or temporary file;
- sensitive local asset;
- undecided.

Each item must record owner, rationale, intended disposition, and whether it belongs in the external Builder baseline.

### Ahead Commit Review

Review each of the seven local-only commits independently. Freeze:

- canonical Builder branch;
- exact baseline commit;
- commits intentionally included;
- commits intentionally excluded and why.

### P1 Pass

- zero undecided entries;
- every modified and untracked item classified;
- every required source asset has an explicit inclusion decision;
- local, generated, and sensitive assets have a verifiable non-public disposition;
- after a separately authorized execution window, the target worktree is clean with no untracked files.

## P2: Governance Asset Public-Safety Review

The candidate set is conservatively five documents:

1. `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md`
2. `docs/evidence/Vera_Evidence_Manifest_Protocol_v0.1.md`
3. `docs/findings/Presentation_Truth_Guard_RCA_20260727.md`
4. `docs/governance/Vera_Trust_Governance_Closure_20260729.md`
5. `REPOSITORY_SHARE_READINESS_REPORT.md`

The fifth report contains local paths, security findings, and sensitive filenames and must not be presumed public.

### Review Checks

- absolute local paths;
- usernames, email addresses, account identifiers, VIP/customer/PII;
- internal IPs, URLs, topology, and environment details;
- credential values or actionable credential references;
- private provider contracts;
- unsupported runtime, production, or live-capability claims.

Each asset must be labeled:

- PUBLIC;
- INTERNAL;
- REDACT-THEN-PUBLIC.

### P2 Pass

- authoritative required set frozen;
- every asset has reviewer sign-off and publication classification;
- PUBLIC assets contain no sensitive material and make no false runtime claim;
- every required PUBLIC asset is included in the eventual exact remote baseline.

## P3: Reproducible Secret Scan Evidence

Use at least one approved scanner, preferably `gitleaks`; optional corroboration may use `trufflehog` or `detect-secrets`.

Record without secret values:

- tool and version;
- ruleset/config checksum;
- repository and exact commit;
- scan scope;
- timestamp;
- command or invocation profile;
- exit status;
- finding count;
- redacted classifications and reviewer decisions.

Required scopes:

1. target tracked worktree/baseline;
2. full Git history and all relevant refs.

Scanner cleanliness alone is insufficient. P3 must reconcile all findings with the P0 A/B/C/D classification.

### P3 Pass

- target baseline and full history have repeatable scan receipts;
- no unresolved high-confidence finding;
- every scanner finding maps to a reviewed P0 classification;
- allowlists and false-positive decisions have reviewer rationale.

## Execution Sequence

```text
P0 Secret Review
  -> P1 Boundary Classification
  -> P2 Public-Safety Review
  -> P3 Reproducible Scan
  -> separately authorized minimal commit/sync window
  -> independent Share Readiness re-audit
  -> separate onboarding and permission decision
```

Do not force push. If history rewrite becomes necessary, open a separate high-risk window only after affected secrets are rotated and forks, clones, caches, and downstream users are assessed.

## Final Acceptance

All requirements must be independently proven:

- canonical branch and exact baseline SHA frozen;
- `HEAD == @{upstream}`, ahead 0, behind 0;
- clean worktree and no untracked files;
- all seven commits, 17 modifications, and 27 untracked entries dispositioned;
- required PUBLIC governance assets included in the remote baseline;
- P0 contains no UNKNOWN or active A secret;
- privacy and account exposure closed;
- baseline and full-history scanner receipts PASS;
- manual security review PASS;
- same remote SHA can be freshly retrieved;
- Builder-required source and startup assets are complete;
- pending invitations are not treated as readiness evidence;
- Production Ready and production access remain separate gates.

Final report:

```text
Repository Share Readiness:
  Git Sync:             PASS / FAIL
  Governance Assets:   PASS / FAIL
  Secret Exposure:     PASS / FAIL
  Public Share Safety: PASS / FAIL
  Builder Ready:       YES / NO
```

Any insufficient evidence fails closed.

