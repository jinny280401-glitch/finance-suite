# Credential Remediation Report

Status: `PENDING OWNER DECISION`
Scope: public `origin/main` history only; no credential values reproduced.

## Evidence

Tool: `gitleaks 8.30.1`
Command scope: `origin/main` history (`90` commits, approximately `1.35 MB`)
Result: `FAIL` with `2` redacted `generic-api-key` findings.

| Finding | Commit | Classification | Owner decision |
|---|---|---|---|
| `scripts/tushare_data.py:13` | `5b04fa0` | `UNKNOWN` | Identify issuer and rotation status |
| `docs/MCP_TOOLS_GUIDE.md:571` | `aa5f06f` | `UNKNOWN` | Identify issuer and rotation status |

The scanner proves that public history contains values matching a credential rule. It does not by
itself prove whether either value is active, invalid, a placeholder, or a documentation example.

## Required Owner Decisions

For each finding, record:

- credential owner/provider;
- `ROTATED`, `ACTIVE`, or `UNKNOWN`;
- whether revocation is required;
- whether history remediation is required;
- authorization for any history rewrite or equivalent public remediation.

Until these fields are resolved, `Secret Exposure` remains `FAIL` and no clean attestation may be
issued.
