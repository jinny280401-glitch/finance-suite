# INCIDENT RCA CARD — Invoice Function Issue

**Date of RCA**: 2026-07-30
**Source of Truth (SOT)**: `/Users/Zhuanz/finance-suite/` (working tree at HEAD `cdac1ca docs(memory): record fusion audit freeze`)
**Scope**: Read-only. No code change. No deploy. No architecture change.

---

## 0. Critical RCA Finding (read this first)

**The "Invoice function" does not exist in the finance-suite production codebase.**

This is not a hypothesis. It is the result of an exhaustive search across the SOT:

- **Frontend (`app/`)**: 26 HTML pages including `auction.html`, `stock.html`, `workbench-config.html`, `meeting.html`, etc. **No `invoice.html`, no `fapiao.html`, no `bill.html`, no `receipt.html`.**
- **Backend (`server_scripts/`)**: 4 Python modules — `auth.py`, `intel_api.py`, `watchlist_api.py`, `manage_users.py`. **No `invoice_api.py`.**
- **MCP server (`mcp_server.py`)**: tools enumerated in the docstring at line 23 — `market_pulse`, plus others. **No `invoice` tool, no `fapiao` tool.**
- **Grep across active code**: `grep -riE "invoice|fapiao|报销|发票|票据|receipt" app/ server_scripts/ mcp_server.py scripts/` returned **zero non-roadshow hits**. The only matches are in `roadshow-2026-06/*` marketing/pitch material (mentions "报销" as a future Skill category, not as an active function).
- **Git history**: `git log --all --grep="invoice\|fapiao\|报销\|发票"` returned **zero commits**.
- **Branches**: no branch name contains `invoice`, `fapiao`, `bill`.

The remaining RCA sections below therefore have nothing to populate from production. They are filled with `NOT PRESENT IN PRODUCTION` markers rather than fabricated values.

---

## 1. User Symptom

User reports: "Invoice function issue" — some form of trouble with an invoice function on production `touziagent.com`. Exact failure mode is **not specified** in the request, and **the function it refers to cannot be located in the SOT**.

Possible interpretations of the symptom (none currently verified):
- Misremembered feature name — user is thinking of a different system.
- Planned-but-not-built feature — "报销" (reimbursement/invoice) is referenced as a future Skill in `roadshow-2026-06/AI大赛成果-Vera-完整版.md` ("业务推进表/报销/会议记录/董事会/写稿等 5 个非金融 Skill 已经在跑") but no production code corresponds.
- Different system entirely — the 报销Skill distribution (per memory `project_reimbursement_skill_distribution.md`) is a separate Claude Skill workflow with template files at `~/Downloads/接待审批单（空）.docx`, not part of the finance-suite web app.
- Alias collision — "invoice" might be a user-side nickname for some other finance-suite feature (e.g., 票据, 结算单, 报告 PDF), none of which were located by the search.

## 2. Frontend Entry

**NOT PRESENT IN PRODUCTION.**

- No HTML page in `/Users/Zhuanz/finance-suite/app/` corresponds to any invoice/receipt/invoice-like function.
- `app/auction.html`, `app/stock.html`, `app/meeting.html`, `app/workbench-config.html`, etc. — none are invoice-related.
- No navigation entry in any existing HTML page (grep across `app/*.html` for any invoice-related link text or href) returns nothing.

## 3. API Endpoint

**NOT PRESENT IN PRODUCTION.**

- `server_scripts/intel_api.py` contains no invoice endpoint (grep `invoice|fapiao|bill|receipt` against this file: 0 hits).
- `mcp_server.py` registers no invoice tool (line 23 lists available tools: none named invoice or fapiao).
- No `/api/invoice*` route, no `/api/fapiao*` route.

## 4. Backend Route

**NOT PRESENT IN PRODUCTION.**

- `server_scripts/` contains only `auth.py`, `intel_api.py`, `watchlist_api.py`, `manage_users.py`, `__pycache__/`, `import_accounts.sh`. None implement any invoice function.
- No `invoice_data.py`, `invoice_service.py`, or equivalent module in `scripts/` either.

## 5. Provider Dependency

**NOT PRESENT IN PRODUCTION.**

- No invoice-related provider call exists in `scripts/` or `mcp_server.py`.
- The only "provider" concept in finance-suite is `ProviderClass` for institutional market data (Wind / Choice / iFinD / Tushare / AkShare), used for market data — not invoices.

## 6. Database Dependency

**NOT PRESENT IN PRODUCTION.**

- finance-suite does not use a relational database for invoice storage.
- (Note: `watchlist_api.py` uses local file JSON for watchlists; auth uses a user store. Neither is invoice-related.)

## 7. Last Known Working State

**NEVER WORKING — feature never existed in the production codebase.**

- No git commit introduces or modifies any invoice functionality (`git log --all --grep="invoice\|fapiao\|报销\|发票"`: 0 results).
- No branch contains invoice work.
- The only references to "报销" appear in roadshow marketing content (`roadshow-2026-06/AI大赛成果-Vera-完整版.md`, `roadshow-2026-06/太子讨论总结-20260618.md`, etc.) where it is listed as a **future Skill**, not a deployed function.

## 8. Root Cause Classification

**Primary classification: `USER_SYMPTOM_MISMATCH` / `FEATURE_NEVER_DEPLOYED`**

The reported symptom refers to a function that does not exist in the SOT. The root cause is therefore one of:

1. **Symptom refers to a feature in a different system.** The user may be confusing finance-suite production with the 报销Skill (a separate Claude Skill workflow documented in memory `project_reimbursement_skill_distribution.md`) or with another tool entirely.
2. **Symptom refers to a planned-but-not-built feature.** The "报销" Skill is mentioned in roadshow material as a future capability, but no production code has been written.
3. **Symptom refers to an invoice-like function under a different name.** Search for synonyms (票据, 结算单, 报告 PDF, 报价单) returned no hits either, but if the user can supply the actual feature name, this RCA can be redone.
4. **Symptom refers to a feature that was removed in a prior commit.** No such removal commit was found in git history, but this possibility cannot be 100% ruled out without a deeper audit of every commit's diff.

**Most likely root cause (single-line)**:
> The "Invoice function" is not implemented in the finance-suite production codebase; the user symptom refers to a feature that does not exist or is named differently than reported.

## Sign-off

| Aspect | Statement |
|---|---|
| Scope | Read-only. No code modified. No deployment attempted. No architecture changes. |
| Evidence basis | File reads + grep + git log + memory recall. |
| Critical limitation | This RCA cannot fix or RCA a function that does not exist. Confirmation of the user's intended feature name is required before any actionable next step. |
| Recommended next step (out of scope for this RCA) | Ask the user: (a) the exact URL or feature name they saw on production; (b) the precise failure mode (404? blank page? error toast?); (c) whether the symptom is in finance-suite production, the 报销Skill workflow, or another system. |

## Boundary Note

Per CLAUDE.md ("先想清楚再动手", "Engram 拒收规律 v2", "遇到问题追根因，不打补丁"), this RCA intentionally surfaces the non-existence rather than fabricating plausible invoice-related fields. Fabricating API endpoints, backend routes, or provider dependencies for a non-existent feature would have produced a misleading artifact that future audits would inherit.
