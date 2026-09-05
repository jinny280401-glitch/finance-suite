# Runtime Governance Validation v0.2 — Window Declaration

**Window:** Runtime Governance Validation v0.2
**Baseline:** `cefc660` (main, tag `v0.1-main-consolidation`)
**Branch:** `runtime-validation-v0.2` (to be cut from `cefc660`)
**Mode:** Validation Only
**Status:** OPEN
**Date:** 2026-08-05
**Predecessor:** v0.1 CLOSED 2026-08-03 (commit `80c1cb2`, tag `v0.1-runtime-validation-final`)

---

## 1. Why v0.2 Exists

v0.1 已 CLOSED 于 2026-08-03,不修改历史窗口、不重新定义历史 verdict。

v0.2 的存在理由:**v0.1 在 Validation Only 模式下识别出了 15 条 UNKNOWN(9 UA + 6 UB),其中 Track A 的 9 条里有部分项具备纯静态验证条件,而 v0.1 因报告窗口已 CLOSED 无法再展开。** v0.2 不是修正 v0.1 的结论,而是在 v0.1 划定的 UNKNOWN 边界内,补做能做的部分。

## 2. Scope

### In Scope

- **Runtime Evidence completeness** — Track A 的 9 条 UA UNKNOWN 中,哪些可以通过重读 `cefc660` 基线代码 + 已有 evidence 文件被静态判定,哪些必须 live production access。
- **Root Cause Evidence** — 7/17 Auction hotfix 在 Web path 上的部署证据链(incident → fix → deployment → runtime observed → evidence captured → root cause proven 五项表的逐项复核)。
- **Fix deployment state** — MCP path 的 auction_data.py 修复部署状态、是否存在 hotfix 等同物。
- **Claim boundary** — v0.1 报告结尾 "Local runtime evidence ≠ Production runtime evidence / Fix exists ≠ Root cause proven / HTTP 200 ≠ Business success" 三条治理区分在 v0.2 验证动作下是否依然成立。

### Out of Scope

- 不修改 v0.1 的任何文件、commit、tag、verdict。
- 不重新定义 v0.1 报告里的历史结论。
- 不进入代码修复(Validation Only)。
- 不进入生产部署(无 deployment authorization)。

## 3. Track 划分

### Track A — Auction P0 Runtime Validation (Active)

继承 v0.1 报告 §2 的 9 条 UA UNKNOWN:

| ID | Item | 静态可达性 | v0.2 行动 |
|---|---|---|---|
| UA-F1 | HTML response source at incident time | NO | UNKNOWN carry-forward |
| UA-F2 | Original request ID | NO | UNKNOWN carry-forward |
| UA-F3 | Response headers/body during failure | NO | UNKNOWN carry-forward |
| UA-F4 | Exhausted connections trigger | NO | UNKNOWN carry-forward |
| UA-F5 | scripts/app parity as root cause | PARTIAL | 静态对照 `scripts/auction_data.py` 与 `app/auction.html` 数据流 |
| UA-F6 | Post-2026-07-24 production retest | NO (needs live access) | UNKNOWN carry-forward |
| UA-F7 | `market_context` module resolution | **YES** | 基线 grep + git history 追溯 |
| UA-F8 | Backend deployment mechanism | **YES** | `deploy.sh` 已确认只覆盖 `app/*.html`;追查后端独立部署链 |
| UA-F9 | Which path served production incident traffic | NO (needs live access) | UNKNOWN carry-forward |

### Track B — Scheduler Model Resolution (Deferred)

v0.1 报告 §3 标记的 6 条 UB UNKNOWN 全部保持不变。Track B 在 v0.2 不展开,等待 Track A 收口后再评估是否需要 v0.3 专门窗口。

## 4. Locked Assets (不可修改)

- `docs/governance/EVIDENCE_GOVERNANCE_v1.0.md` — FROZEN 2026-08-03
- `docs/governance/Trust_Gate_v1` 及其实现
- Multi-Agent Trust Gate v1
- `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md` — Capability Maturity Ladder L0-L6
- Canonical Main Structure (`cefc660`)
- v0.1 报告 + 全部 commit / tag / evidence 文件

## 5. Mode Discipline

Validation Only 边界:

- 允许:Read / Grep / Bash(git log / grep / find / sha256sum)/ git 操作(切分支、commit 验证报告)
- 允许:在 `docs/reviews/` 与 `windows/` 下新建文档
- 允许:重读基线文件、复算 SHA-256、追溯 git 历史
- 禁止:`Edit` / `Write` 修改任何生产路径代码
- 禁止:触发任何部署脚本(`deploy.sh` 在验证环境无授权执行)
- 禁止:声称 capability 升级到 L4+ 除非独立 runtime verification 跑通

## 6. v0.2 Acceptance Criteria

窗口关闭时必须给出:

1. **9 条 UA UNKNOWN 状态表** — 每条标注 RESOLVED / PARTIAL / UNKNOWN(CARRIED) / DEFERRED。
2. **静态可验证项的 evidence** — UA-F5/F7/F8 的代码 / 文档 / git 追溯结果,SHA-256 标注。
3. **Runtime observed 重核** — v0.1 已捕获的 `4532569999bdd12e9863c1c835893b982f3c2ce95d69ebd9d6520d236263eac0` 与 `72a17651b6a8885a228c64181ecb9c72e9bab0abc40c4edf01a49e7df1bfbff4` 在 `cefc660` 基线里依然存在且 hash 不变。
4. **Claim boundary 重审** — 三条治理区分(Local runtime ≠ Production / Fix exists ≠ Root cause proven / HTTP 200 ≠ Business success)是否需要新增第四、第五条。
5. **Window Handoff** — 按 `feedback_window_handoff_convention.md` 规范生成 `windows/RUNTIME_GOVERNANCE_VALIDATION_v0.2_HANDOFF.md`,同步 Engram + Memory。

## 7. Next Window Recommendations(预留)

v0.2 不预先承诺 v0.3 内容。窗口关闭时根据 UNKNOWN 残量决定:

- 若 UA-F6/F9 仍需 live access → 提议 v0.3 为 Deployment Authorization Window(需 G 显式授权)。
- 若 Track B 在 v0.2 期间仍无人启动 → 提议 v0.3 = Model Identity Attestation Window(Model Identity Attestation 链是 v0.1 报告 §7 第一条 prereq)。

---

**End of Declaration**