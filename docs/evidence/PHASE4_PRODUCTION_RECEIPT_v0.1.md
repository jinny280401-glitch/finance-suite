# Phase 4 Production Receipt — v0.1

**date:** 2026-08-20
**authority:** Repository Handoff Closure v0.1（G 路由：C 提供原始只读 SSH stdout → Session A 脱敏物化 + 独立本地复核）
**session role:** Session A — Read-only Reviewer（未 SSH 生产；仅本地 git SHA-256 复核）
**scope:** 生产 landing 目录 6 个采样文件的身份判定。**不覆盖整棵生产 app tree**（见 §6 边界）。

---

## 1. C 的原始只读 SSH transcript（脱敏，逐字未改）

```
[OBS-1] SSH baseline — exit 0
<host>: accessible
effective user: <user>
working directory: <landing-parent>

[OBS-2] Active service — exit 0
finance-suite.service: active/running
WorkingDirectory=<landing>
ExecStart=<landing>/venv/bin/uvicorn app.main:app … --workers 4
FragmentPath=<systemd-unit>

[OBS-3] Landing identity — exit 0
<landing>/.git: ABSENT
=> deploy target, not a Git repository

[OBS-4] Production file hashes — exit 0
a7b8f1396eb8a91e9da5d2ef4d3b3c8b9969d11515c436a588ce181b045bb18e  <landing>/mcp_server.py
d395249e7dff4050cb88a953ed0b54b27620cae0cb0177f8cd0a5e17e3d81a3c  <landing>/scripts/auction_data.py
baaca1e53ee47802796ec00d14fbe3d9a664dbe2ef00692c30e3424de14d2bd5  <landing>/app/auction_data.py
2b4469a91e8efc0920ad57c765c310552f46049d9564a28b36e7f715e12b8ac4  <landing>/app/stock_data.py
59166f29d52caca213c635d34076156735e59312d1ebb6e9244be62765c0840a  <landing>/templates/index.html

[OBS-5] Deploy mechanism — exit 0
deployed *deploy*.sh count: 0
systemd/cron deploy-reference search: no result

[OBS-6] Full app Python-tree comparison — comparison completed
production: 23 Python files
backend HEAD: 24 Python files
drift:
- <landing>/app/routers/api.py hash 818b7d6e…09001b50
  backend HEAD hash a37715de…0844af06
- backend HEAD app/search_trust_gate.py absent from production
```

---

## 2. Session A 独立本地复核（git SHA-256，逐字）

比对基线 = 本地 git 对象（非生产）。命令 `git show <ref>:<path> | shasum -a 256`。

```
backend main = e266213768f7429791f1de3f35b5ff6b416f84c0   (rev-parse main == e266213: YES)

e266213:mcp_server.py            a7b8f1396eb8a91e9da5d2ef4d3b3c8b9969d11515c436a588ce181b045bb18e
e266213:app/auction_data.py      baaca1e53ee47802796ec00d14fbe3d9a664dbe2ef00692c30e3424de14d2bd5
e266213:app/stock_data.py        2b4469a91e8efc0920ad57c765c310552f46049d9564a28b36e7f715e12b8ac4
e266213:app/routers/api.py       818b7d6e30dcfce17fecf06d7e580578fe718d6cd2d103eae41ec9bf09001b50
e266213:templates/index.html     59166f29d52caca213c635d34076156735e59312d1ebb6e9244be62765c0840a
e266213:scripts/auction_data.py  NOT-in-e266213（e266213 无 scripts/ 目录）

frontend fcafa4d:scripts/auction_data.py  d395249e7dff4050cb88a953ed0b54b27620cae0cb0177f8cd0a5e17e3d81a3c
frontend main/rv-v0.1/fcafa4d:templates/index.html  （路径不存在，git show 空输出）
backend fix/search-trust-gate-p0:app/search_trust_gate.py  695c46c801ac9152c86b148614a5290e70bb6cd76f79d9253d5d20c6ac714fef

backend 8a88685:app/routers/api.py  a37715de9db9d05b48d8e4552ea1116db5b6b068919f42b585ff9ae0844af06f
backend 52a6d56(fix HEAD):app/routers/api.py  7771ae101c29c2d09cba1eb0b9ea634664a317f6dda5287723a5fd837eb0a6bb
```

---

## 3. 比对矩阵（生产 hash vs 本地 ref hash）

| 生产文件 | 生产 hash | 本地匹配 ref | verdict |
|---|---|---|---|
| `mcp_server.py` | `a7b8f139…` | **e266213 (main)** | MATCH main |
| `app/auction_data.py` | `baaca1e5…` | **e266213 (main)** | MATCH main |
| `app/stock_data.py` | `2b4469a9…` | **e266213 (main)** | MATCH main |
| `app/routers/api.py` | `818b7d6e…` | **e266213 (main)** | MATCH main |
| `templates/index.html` | `59166f29…` | **e266213 (main)** | MATCH main |
| `scripts/auction_data.py` | `d395249e…` | **frontend `fcafa4d`** | DRIFT（历史 frontend，非 backend） |

**5/6 采样文件 = backend main e266213；1/6 = 历史 frontend fcafa4d。**

---

## 4. 关键发现：C 的 OBS-6 基线错误（已用 hash 反证）

C 的 OBS-6 声称 `api.py` production(`818b7d6e`) ≠ backend HEAD(`a37715de`)，判为 drift。本地复核：

- `a37715de…0844af06` = **commit `8a88685`** 的 api.py（`8a88685` = `fix/search-trust-gate-p0` 分支首个 commit，其 parent 正是 e266213）。
- 因此 C 的"backend HEAD"实为 **`fix/search-trust-gate-p0` 分支**（backend 仓库当前 checkout 的分支），**不是 main e266213**。
- 同理，OBS-6 的"backend HEAD 有 search_trust_gate.py、production 缺失"——search_trust_gate.py 只在 fix 分支，main e266213 **同样没有**。

**以正确基线 main e266213 重比：**
- `api.py`：production `818b7d6e` == e266213 `818b7d6e` → **MATCH，非 drift**。
- `search_trust_gate.py`：production 无，e266213 也无 → **一致，非 drift**。

结论：C 把「相对未合并分支 fix/search-trust-gate-p0 的差异」误报为「相对 main 的生产漂移」。

---

## 5. 修正后 verdict

- **生产 6 采样文件 = backend main e266213（5 个）+ 历史 frontend fcafa4d 遗留（scripts/auction_data.py，1 个）。**
- production `api.py`、`search_trust_gate.py` 相对 main **无漂移**。
- 唯一真实漂移 = `scripts/auction_data.py`（frontend fcafa4d 遗留文件，backend main 无此路径）。
- **仍是 mixed-revision，但比 C 原判更干净**：生产 ≈ e266213 + 一个 frontend 遗留脚本，而非"api.py 漂移 + trust-gate 缺失"的双重漂移。

**三分离（G 定精度）对 mcp_server.py / auction_data.py / stock_data.py 仍成立：**
- 文件身份 = backend e266213 MATCH（**现已独立 SHA 复核，PROVEN**）
- runtime consumption = UNKNOWN（systemd 只启动 `app.main:app`，mcp_server.py 是否被独立消费未证）
- canonical ownership = UNDECIDED（production presence ≠ ownership 推断）

---

## 6. 边界 / 未覆盖（明确不做）

- **只覆盖 6 个采样文件**。`app/main.py`、`app/routers/intel.py` 不在 raw receipt（C 未给生产 hash），其"MATCH"仅来自更早的二手摘要，**本 receipt 不背书**。
- 文件计数 production 23 .py vs e266213 31 .py：构成差异未逐一比对，**不证明"整棵生产树 = e266213 子集"**。scripts/auction_data.py 是已知多出来的非 backend 文件。
- **移动基线**：backend `fix/search-trust-gate-p0` 在本次会话期间从 `5a523e0` 推进到 `52a6d56`（另有 session 在提交）。本 receipt 的比对基线固定为不可变的 **e266213**，不受该分支移动影响。
- **OBS-5**：生产未发现 `*deploy*.sh` 部署痕迹，与历史 `deploy.sh`/`deploy-backend.sh` 的"部署方向声明"是否一致 = 未证。

---

## 7. 支持 / 不支持

- **支持**：auction_data.py + stock_data.py + mcp_server.py + api.py + templates/index.html 的生产文件身份 = backend main e266213（SHA-256 独立复核）。
- **不支持**：以本 receipt 作 **Phase 2 ownership 裁决**——文件身份 PROVEN 不等于 ownership DECIDED；且 scripts/auction_data.py 的 frontend 遗留、main.py/intel.py 未采样、OBS-5 部署机制未证，均未闭合。

**Phase 2 继续暂停。**
