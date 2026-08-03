# Configuration & Identity Audit v0.1

**Audit time:** 2026-07-31T16:07:05+08:00  
**Mode:** READ-ONLY  
**Target:** Vera / Finance Suite local, production, and adjacent Linmeimei agent identity surfaces  
**Status:** COMPLETE WITH FINDINGS  
**Production mutation:** NONE  
**Secret values:** NOT COLLECTED / NOT RECORDED

## 1. Scope and Boundary

This audit establishes the currently observable Vera Runtime identity boundary. It maps credential metadata, provider identities, execution identities, local/production drift, and governance gaps. It does not validate provider entitlements, test secret validity, rotate credentials, change configuration, deploy code, restart services, or fix runtime behavior.

```text
Credential name observed
  != credential valid
  != credential authorized
  != credential loaded
  != provider invoked
  != provider result attributable
  != evidence qualified
  != production capability proven
```

Identity layers used in this report:

```text
Human / operator identity
  -> infrastructure access identity
  -> host and service identity
  -> application route identity
  -> provider identity
  -> credential alias / version identity
  -> provider execution identity
  -> evidence identity
  -> claim identity
```

## 2. Evidence Register

Only metadata and source/configuration references were inspected. Secret values were suppressed.

| ID | Authoritative surface | Evidence recorded |
|---|---|---|
| `E-CI-01` | `/Users/Zhuanz/finance-suite/.env`, `.env.save`, `.env.example` | File owner/mode/mtime, variable names, SET/ABSENT state; values not printed. |
| `E-CI-02` | Local shell environment | `TAVILY_KEYS`, `BRAVE_KEYS`, and `SUPADATA_API_KEY` names are present in the current process environment; values not printed. |
| `E-CI-03` | `/Users/Zhuanz/finance-suite` source | Local research demo references `OPENROUTER_API_KEY`; data adapters reference JQData, iFinD, Choice, Supadata, Tavily, Brave, and Tushare identities. |
| `E-CI-04` | `/Users/Zhuanz/Documents/New project 6/Linmeimei-Agent` | Claude Code CLI is the model execution mechanism; Docker design persists `/root/.claude`; application credentials are environment variables. |
| `E-CI-05` | Local `claude auth status` | Claude CLI reports `loggedIn=true`, `authMethod=oauth_token`, `apiProvider=firstParty`; no token was displayed or retained. |
| `E-CI-06` | Production host metadata | Runtime host verified through Tencent Cloud metadata: region `ap-seoul`, public IP `119.28.156.125`; instance ID presence confirmed but redacted. |
| `E-CI-07` | Jump host metadata | SSH jump host `8.138.2.55` reports Alibaba Cloud region `cn-guangzhou`; instance ID presence confirmed but redacted. |
| `E-CI-08` | Production `finance-suite.service` | Service runs as `ubuntu:ubuntu`, `DynamicUser=no`, working directory `/home/ubuntu/finance-suite-web`, four Uvicorn workers on `127.0.0.1:8000`. |
| `E-CI-09` | Production `.env` and source | Environment variable names, file custody/mode, consumers, Qwen endpoint and model name inspected; credential values suppressed. |
| `E-CI-10` | Production `app/config.py`, `app/llm.py`, `app/routers/api.py` | Qwen/DashScope is the active report-generation LLM path; Tavily/Brave search and JWT signing identities are configured. |
| `E-CI-11` | Production Nginx and TLS metadata | Public ingress `touziagent.com` / `www.touziagent.com` / `api.touziagent.com`; Let's Encrypt certificate metadata and key permissions inspected. |
| `E-CI-12` | Production filesystem and Git probe | Deployment directory is not a Git worktree; selected deployed source SHA-256 values recorded during inspection, but no canonical commit identity exists on-host. |
| `E-CI-13` | Gitleaks metadata-only scan of `/Users/Zhuanz/finance-suite` | A tracked local source file contains a 56-character hard-coded default for `TUSHARE_TOKEN`; value was not recorded. |

Selected production artifact fingerprints at audit time:

| Artifact | SHA-256 |
|---|---|
| `app/config.py` | `7c459a202b481afdac80ef3ac041287fd1afbdcf63d5444816ef9113b0ab49ec` |
| `app/llm.py` | `93d21a6c324b1fef9c20736d1c32a5c9ffe6487de7a34f06248b4ac4cbc923ad` |
| `app/routers/api.py` | `2f78db6f78b85e3083efe0582868d5799cf6197075c049c43097888aea127889` |

These hashes identify inspected files only; they are not a release manifest.

## 3. A. Credential Metadata Inventory

`PRESENT` means a non-empty value was observed through metadata inspection. It does not establish validity, ownership, authorization, freshness, or runtime use.

| Credential / identity | Local state | Production state | Storage / consumer | Account owner | Rotation / expiry |
|---|---|---|---|---|---|
| `OPENROUTER_API_KEY` | PRESENT in local Finance Suite `.env` | ABSENT | Local `scripts/research_demo_api.py` / research digest path | UNKNOWN | UNKNOWN |
| `QWEN_API_KEY` | ABSENT from inspected local Finance Suite `.env` | PRESENT | Production `.env` -> `app.config` -> `app.llm` | UNKNOWN | UNKNOWN |
| `QWEN_API_URL`, `QWEN_MODEL` | ABSENT locally | PRESENT | Production endpoint/model selection | Config custodian observable; decision owner UNKNOWN | N/A / change history UNKNOWN |
| `TAVILY_KEYS` | PRESENT in current shell; absent from local `.env` | PRESENT, pool count `10` | Search provider, round-robin selection | UNKNOWN | UNKNOWN |
| `BRAVE_KEYS` | PRESENT in current shell; absent from local `.env` | PRESENT, pool count `3` | Search provider/fallback, round-robin selection | UNKNOWN | UNKNOWN |
| `SUPADATA_API_KEY` | PRESENT in current shell; absent from local `.env` | PRESENT | Video transcript extraction | UNKNOWN | UNKNOWN |
| `JQDATA_USERNAME`, `JQDATA_PASSWORD` | PRESENT | PRESENT | `scripts/jqdata_fetch.py` | UNKNOWN | UNKNOWN |
| `JQ_USERNAME`, `JQ_PASSWORD` | PRESENT | PRESENT | Legacy/alternate aliases; no active production consumer found | UNKNOWN | UNKNOWN |
| `THS_USERNAME`, `THS_PASSWORD` | PRESENT | PRESENT | iFinD SDK login path | UNKNOWN | UNKNOWN |
| `THS_TOKEN`, `THS_REFRESH_TOKEN` | PRESENT | PRESENT | iFinD HTTP token and refresh path | UNKNOWN | Token expiry/refresh lifecycle not recorded centrally |
| `EM_USERNAME`, `EM_PASSWORD` | PRESENT | PRESENT | Local Choice/EmQuant adapter; no production consumer found | UNKNOWN | UNKNOWN |
| `TUSHARE_TOKEN` | Environment entry absent; tracked source contains a non-empty hard-coded default | Production script absent | Local `scripts/tushare_data.py` | UNKNOWN | UNKNOWN |
| `SECRET_KEY` | ABSENT from inspected local Finance Suite `.env` | PRESENT | Production JWT signing in `app.auth` | Security owner UNKNOWN | UNKNOWN |
| `ACCESS_TOKEN_EXPIRE_HOURS` | ABSENT locally | PRESENT | Production JWT lifetime policy | Policy owner UNKNOWN | Policy history UNKNOWN |
| Claude Code OAuth identity | Local CLI authenticated through first-party OAuth | Production Vera host has no Claude CLI | Local `~/.claude`; Linmeimei Docker design uses named volume `linmeimei-claude-auth` | Human/account owner not established by this audit | OAuth lifecycle UNKNOWN |
| `FEISHU_APP_ID`, `FEISHU_APP_SECRET` | Example only in Linmeimei repo; actual `.env` not found | Not part of Vera production `.env` | Linmeimei messaging integration | UNKNOWN | UNKNOWN |
| WeCom / WxPusher / MiniMax / `ENCRYPTION_KEY` | Example only in Linmeimei repo; actual `.env` not found | Not part of Vera production `.env` | Linmeimei integration/runtime | UNKNOWN | UNKNOWN |
| `GILDATA_ACCESS_TOKEN` / `GILDATA_API_KEY` | Example/config reference only; no local value found | Not found | Proposed Gildata adapter, runtime status `PENDING` | UNKNOWN | UNKNOWN |
| SSH private key | Local file present | N/A | Operator -> Alibaba jump host -> Tencent production host | Local filesystem custodian `Zhuanz`; authorization owner UNKNOWN | UNKNOWN |
| TLS private key | N/A | PRESENT | Nginx public ingress | Filesystem owner `root`; certificate issuer Let's Encrypt | Certificate expires 2026-09-23; Certbot timer enabled and active |

### 3.1 Credential File Custody

| Surface | Mode | Custodian evidence | Finding |
|---|---|---|---|
| Local `/Users/Zhuanz/finance-suite/.env` | `0644` | `Zhuanz:staff` | Contains credentials and is readable by other local accounts. |
| Local `.env.save` | `0600` | `Zhuanz:staff` | Restricted, but carries legacy JQ aliases without lifecycle metadata. |
| Production `/home/ubuntu/finance-suite-web/.env` | `0644` | `ubuntu:ubuntu` | Contains all production provider/auth credentials and is readable by other host accounts. |
| Local SSH private key | `0600` | `Zhuanz:staff` | File permissions are restricted; rotation/authorization metadata is absent. |
| Production TLS private key target | `0600` | `root:root` | Restricted and separated from application user. |

Filesystem custody is not provider-account ownership. No inspected registry binds a credential to an accountable business owner, issuer, purpose approval, issue date, expiry, last rotation, next rotation, or revocation procedure.

## 4. B. Provider Identity Mapping

### 4.1 Runtime and Infrastructure Chain

```text
Public user
  -> DNS / HTTPS: touziagent.com
  -> Nginx + Let's Encrypt identity
  -> Tencent Cloud VM (ap-seoul, 119.28.156.125)
  -> systemd finance-suite.service
  -> OS identity ubuntu:ubuntu
  -> Uvicorn app.main:app, 4 workers, 127.0.0.1:8000
  -> application route / skill
  -> provider adapter
  -> credential loaded from production .env
  -> provider response
  -> report / source list / QC output
```

Administrative access is a separate chain:

```text
Local operator + local SSH key
  -> Alibaba Cloud jump host admin@8.138.2.55 (cn-guangzhou)
  -> Tencent Cloud runtime host ubuntu@119.28.156.125 (ap-seoul)
```

### 4.2 Provider Map

| Provider identity | Environment | Credential identity | Runtime consumer | Observed status |
|---|---|---|---|---|
| Alibaba DashScope / Qwen | Production | `QWEN_API_KEY` | `app.config` -> `app.llm` -> `/api/analyze`; endpoint `dashscope.aliyuncs.com`, model `qwen-plus` | CONFIGURED and wired; credential validity not tested |
| OpenRouter | Local demo | `OPENROUTER_API_KEY` | Local research digest/demo path | LOCAL ONLY; not production LLM identity |
| Anthropic Claude Code | Local / Linmeimei design | First-party OAuth state, not an Anthropic API key in application config | `app.services.agent.ask_claude` invokes `claude` CLI | LOCAL AUTH OBSERVED; absent from Vera production host |
| Tavily | Local shell and production | `TAVILY_KEYS` | Search routes via key pool | CONFIGURED; per-request key alias/execution ID not emitted |
| Brave | Local shell and production | `BRAVE_KEYS` | Search route/fallback via key pool | CONFIGURED; actual provider selection not emitted consistently |
| Supadata | Local shell and production | `SUPADATA_API_KEY` | Video transcript extraction | CONFIGURED; runtime invocation not tested |
| JQData | Local and production | `JQDATA_USERNAME`, `JQDATA_PASSWORD` | `scripts/jqdata_fetch.py` | CREDENTIAL + CONSUMER OBSERVED; request use not proven |
| iFinD | Local and production | Account/password and token/refresh-token identities | `scripts/ifind_data.py` | MULTIPLE AUTH MODES; selected mode not centrally declared |
| Choice / EmQuant | Local consumer; credentials also present in production | `EM_USERNAME`, `EM_PASSWORD` | Local `scripts/emquant_data.py`; no production source consumer found | PRODUCTION CREDENTIAL WITHOUT OBSERVED CONSUMER |
| Tushare | Local source | `TUSHARE_TOKEN` with hard-coded default | Local `scripts/tushare_data.py` | CREDENTIAL-LIKE SOURCE DEFAULT; production path absent |
| AkShare / Eastmoney | Local and production | No credential observed for normal SDK/HTTP path | Structured market-data and research routes | PROVIDER FAMILY INFERABLE; execution identity incomplete |
| Gildata / 聚源 | Local proposal/adapter only | Example token identity | `scripts/gildata_adapter.py`, marked `PENDING` | NOT A VERIFIED RUNTIME PROVIDER |

### 4.3 Linmeimei Is a Separate Model Identity Boundary

The Linmeimei agent code does not call the production Qwen client. It invokes the Claude Code CLI and relies on persistent Claude OAuth state. Its Docker design mounts `/root/.claude`, while the current Vera production host has neither Docker nor Claude CLI installed. Therefore:

```text
Vera production LLM identity = Qwen / DashScope API credential
Linmeimei agent LLM identity = Claude Code first-party OAuth state
```

These identities must not be presented as interchangeable or as a single deployed model layer.

## 5. C. Local vs Production Drift

| Dimension | Local / proposal state | Production effective state | Drift finding |
|---|---|---|---|
| LLM provider | OpenRouter local research demo; Claude Code for Linmeimei | Qwen Plus through Alibaba DashScope | CONFIRMED provider identity drift |
| Runtime host | Developer macOS workspaces | Tencent Cloud VM in `ap-seoul` | Expected environment separation; identity must be explicit |
| Administrative path | Local SSH identity through Alibaba Cloud jump host | Service executes on Tencent host as `ubuntu` | Operator identity and runtime identity are separate |
| Source identity | `/Users/Zhuanz/finance-suite` is Git commit `16fc7da...`; workspace root is another Git commit; Linmeimei is a separate repository | `/home/ubuntu/finance-suite-web` is not a Git worktree | CONFIRMED release provenance gap |
| Credential source | Local `.env`, current shell, Claude OAuth files, and examples are split across surfaces | One production `.env` is loaded by application code | CONFIRMED configuration-source drift |
| Search key pools | Current shell contains search identities; local Finance Suite `.env` does not | Production has 10 Tavily and 3 Brave entries | CONFIRMED source-of-truth ambiguity |
| Choice credentials | Local adapter consumes `EM_*` | Production `.env` contains `EM_*`, but no production consumer was found | CONFIRMED stale/orphan candidate |
| JQ aliases | `JQDATA_*` and `JQ_*` coexist | Both alias families coexist; consumer reads `JQDATA_*` | CONFIRMED alias ambiguity |
| Tushare | Local tracked source supplies a hard-coded default | Provider script absent from production | Local credential exposure risk, not production capability |
| Linmeimei runtime | Code and Docker design persist Claude OAuth state | No Docker, Claude CLI, or Linmeimei service on Vera host | NOT DEPLOYED to current Vera production runtime |
| Gildata | Adapter/example exists and is marked `PENDING` | No production Gildata credential or consumer found | PROPOSAL != EFFECTIVE STATE |
| Secret file permissions | Local `.env` is `0644` | Production `.env` is `0644` | Same governance weakness in both environments |
| JWT fallback | Production-style source contains a hard-coded fallback string | Production `SECRET_KEY` is present, so fallback is not proven active | Latent fallback risk; effective use not observed |

## 6. D. Key / ID Governance

### 6.1 Current Identity Awareness

| Required identity | Current evidence | State |
|---|---|---|
| Host / cloud identity | Cloud metadata, public IP, region | OBSERVED |
| Service identity | systemd unit, OS user/group, entrypoint | OBSERVED |
| Application route identity | Route/skill is visible in source and response structures | PARTIAL |
| Provider family | Inferable from config and adapter code | PARTIAL / DISTRIBUTED |
| Credential alias | Environment variable name is known | OBSERVED at configuration level |
| Credential version / safe key ID | No canonical non-secret version identifier found | ABSENT |
| Credential owner / approver | No registry found | UNKNOWN |
| Provider request/execution ID | Not consistently emitted into Vera evidence | NOT OBSERVED |
| Evidence ID | Source URLs may be returned, but canonical evidence identity is not consistently present | NOT CLOSED |
| Claim -> evidence -> provider execution mapping | No end-to-end mapping observed | NOT CLOSED |

### 6.2 Potential Drift and Governance Findings

| ID | Severity | Finding | Evidence boundary |
|---|---|---|---|
| `F-CI-01` | HIGH | Production `.env` is mode `0644` while holding provider and JWT credentials. | Permission exposure is proven; unauthorized access is not claimed. |
| `F-CI-02` | HIGH | Local tracked `scripts/tushare_data.py` contains a non-empty 56-character hard-coded default credential. | Credential-like material is proven; current validity and ownership are UNKNOWN. |
| `F-CI-03` | HIGH | Production deployment has no Git commit identity or release manifest on-host. | File hashes identify the inspected state only; reproducible release provenance is not established. |
| `F-CI-04` | MEDIUM | Credential owner, issue date, expiry, rotation, and revocation metadata are absent from inspected surfaces. | Lack of registry evidence is proven; provider dashboards were not inspected. |
| `F-CI-05` | MEDIUM | Production contains unused or ambiguous identity names (`EM_*`, `JQ_*` beside `JQDATA_*`). | Presence and consumer mismatch are proven; intentional retention is UNKNOWN. |
| `F-CI-06` | MEDIUM | Tavily and Brave use pooled round-robin keys without a safe request-level key/version identifier in observed evidence. | Pool configuration is proven; which key handled a request is not attributable. |
| `F-CI-07` | MEDIUM | Local, Linmeimei, and production use three distinct LLM identity mechanisms: OpenRouter, Claude OAuth, and Qwen/DashScope. | Identity drift is proven; no claim is made that this is unintended. |
| `F-CI-08` | MEDIUM | Provider identity is distributed across environment files, source modules, scripts, and runtime routes. | No canonical Provider Registry was found in inspected surfaces. |
| `F-CI-09` | MEDIUM | Credential identity is not joined to provider execution identity and evidence identity. | Current source/response inspection did not expose an end-to-end chain. |
| `F-CI-10` | LOW | JWT source contains a hard-coded fallback secret string, although production has `SECRET_KEY` set. | Latent code path exists; fallback use in production is not proven. |
| `F-CI-11` | LOW | Local `.env` is also mode `0644`. | Local multi-user exposure is possible; actual unauthorized readership is not claimed. |

No remediation was performed. Severity expresses governance priority, not authorization to change runtime state.

### 6.3 Required Governance Record Shape

The following is a governance mapping requirement, not an implementation or schema decision:

```text
credential_alias
  + environment
  + provider
  + accountable_owner
  + approved_purpose
  + issue_time / expiry
  + last_rotation / next_review
  + revocation_path
  + safe_version_id
  + runtime_consumer
  + provider_execution_id
  + evidence_id
```

The current runtime reliably establishes only part of this chain.

## 7. Unknowns

| Unknown | Why unresolved | Effect |
|---|---|---|
| Provider-account owner and approver for each credential | No authorized account registry or provider dashboard was inspected | Filesystem owner cannot be promoted to account owner. |
| Credential validity, entitlement, quota, and revocation state | No provider authentication/session tests were authorized | PRESENT remains configuration evidence only. |
| Last and next rotation dates | No rotation ledger or secret manager metadata was found | Rotation status remains UNKNOWN. |
| Which pooled search key handled a request | No safe key/version ID is emitted | Per-request credential attribution remains open. |
| Whether JQData, iFinD, Choice, Supadata, or Tushare handled a specific production request | No request-linked execution record was inspected | Configured/available cannot become used/proven. |
| Whether production `EM_*` and `JQ_*` aliases are intentionally retained | No canonical provider registry or decision record was found | Potential orphan/stale credentials remain unclassified. |
| Canonical deployment source revision | Production is not a Git worktree and no release manifest was found | File-level hashes cannot establish complete release identity. |
| Linmeimei production OAuth account and volume custody | Linmeimei is not deployed on the Vera production host; only local/design evidence exists | No production Claude identity claim is permitted. |
| Tushare default validity | Secret value and provider account were deliberately not tested | Finding remains exposure metadata, not active-account confirmation. |
| Claim-level evidence lineage | Provider execution IDs and canonical evidence IDs are not joined to report claims | Request -> provider -> evidence -> claim remains open. |

## 8. Final Audit State

```text
Configuration & Identity Audit Window v0.1:
  COMPLETE WITH FINDINGS

Mode:
  READ-ONLY

Credential Metadata Inventory:
  COMPLETE FOR INSPECTED NAMES / PRESENCE / CUSTODY
  INCOMPLETE FOR OWNER / ROTATION / VALIDITY

Provider Identity Mapping:
  PARTIAL / DISTRIBUTED

Local vs Production Drift:
  CONFIRMED

Key / ID Governance:
  PARTIAL

Runtime Identity Awareness:
  HOST + SERVICE OBSERVED
  PROVIDER + CREDENTIAL PARTIAL
  EXECUTION + EVIDENCE + CLAIM CHAIN NOT CLOSED

Production Runtime:
  NOT CHANGED

Capability Claim:
  NOT CREATED
```

Final boundary:

```text
Intent != execution != verified state
Declared state != effective state
Credential present != provider used
Provider used != evidence attributable
Evidence listed != claim mapped
Audit finding != remediation authorization
```
