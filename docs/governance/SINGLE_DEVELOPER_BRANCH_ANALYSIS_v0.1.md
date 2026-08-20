# Single Developer Branch — Phase 3 Analysis

**Date:** 2026-08-20  
**Status:** DECISION REQUIRED

## Current State

### Frontend (`finance-suite`)
- **Current HEAD:** `runtime-validation-v0.1` @ `13e2acd`
- **Main branch:** `faa01d4` (production canonical anchor)
- **Relationship:** HEAD is 6 commits ahead of main, 6 commits ahead of remote
- **Unpushed commits:**
  - `13e2acd` — IMA shared-note path closure + PDF evidence
  - `b8389f2` — Search trust-gate enforcement + daily price provider
  - `5810ff5` — Repository Inventory v0.1 baseline freeze
  - `61003db` — Wind AIFin CLI wrapper v0.4.2
  - `e777b6b` — fefc2d8 review bundle materialization
  - (1 more)

### Backend (`finance-suite-backend`)
- **Current HEAD (at doc write):** `fix/search-trust-gate-p0` @ `52a6d56`（quarantine 分支 `quarantine/2036bf9-wind-identity-contradiction` @ `1ad59ea` 仍存在但非当前 HEAD）
- **Main branch:** `e266213` (production canonical anchor)
- **Relationship:** Current HEAD does NOT contain the quarantined commit `2036bf9` (verified: `git merge-base --is-ancestor 2036bf9 <current-HEAD>` → NOT ancestor). It exists only on the separate `quarantine/2036bf9-wind-identity-contradiction` branch, alongside but not merged into the current branch or `main`.

## Problem

A human programmer cannot be given:
- A branch with 6 unpushed governance commits
- Multiple branches to choose from, one of which (a separate quarantine branch) sits alongside the working branch and must be explained
- Instructions to "check out the right commit"

They need exactly one clean entry point.

## Options

### Option A: Use `main` branches

**Frontend:** `faa01d4`  
**Backend:** `e266213`

**Pros:**
- Both are stated production canonical anchors
- No unpushed governance debt
- No quarantine branch to explain
- Clean entry point

**Cons:**
- Missing 6 commits of governance/inventory work from `runtime-validation-v0.1`
- Repository topology doc (`CANONICAL_REPOSITORY_TOPOLOGY_v0.1.md`) created in this session is not in `main`
- `2036bf9` disposition doc is not in backend `main`

**Resolution path:**
1. Cherry-pick governance docs from `runtime-validation-v0.1` onto `main`
2. Cherry-pick `1ad59ea` (disposition doc only) onto backend `main`
3. Reset HEAD to `main` in both repos
4. Declare `main` as developer branch

---

### Option B: Create `human-handoff-v1` branch

**Start from:** Frontend `main` (`faa01d4`) + Backend `main` (`e266213`)

**Pros:**
- Clear signal this is the handoff point
- Clean separation from historical validation branches
- Can cherry-pick only necessary governance docs
- No unpushed validation work

**Cons:**
- Creates a new branch (more cognitive load)
- Requires explaining why not `main`

**Resolution path:**
1. Create `human-handoff-v1` from both `main` branches
2. Cherry-pick governance docs onto it
3. Declare this as developer branch

---

### Option C: Cleanup `runtime-validation-v0.1`

**Keep:** `runtime-validation-v0.1` @ `13e2acd`

**Pros:**
- Already contains repository inventory and governance docs
- No cherry-picking needed for frontend

**Cons:**
- Name suggests validation work, not development work
- 6 commits ahead of remote (not pushed)
- Backend is on wrong branch entirely (needs hard switch)
- Contains experimental/governance commits not meant for feature development

**Resolution path:**
1. Rename `runtime-validation-v0.1` → `developer-main` or similar
2. Push to remote
3. Switch backend to `main` (`e266213`)
4. Declare these as developer branches

---

## Recommendation

**Option A: Use `main` branches** with selective cherry-picks.

**Reasoning:**
- `main` is the conventional developer entry point
- Production canonical anchors are already `main`
- Governance docs can be cherry-picked cleanly
- Avoids "why are there two main branches" confusion
- Aligns with "one branch policy" — the branch is `main`, period

**Action items:**
1. Cherry-pick governance docs from `runtime-validation-v0.1` onto frontend `main`:
   - `CANONICAL_REPOSITORY_TOPOLOGY_v0.1.md` (created this session)
   - Repository inventory baseline if not already in `main`
2. Cherry-pick disposition doc from backend `quarantine/2036bf9-wind-identity-contradiction`:
   - `docs/reviews/COMMIT_2036bf9_DISPOSITION_v0.1.md` (commit `1ad59ea`)
3. Switch frontend HEAD to `main`
4. Switch backend HEAD to `main`
5. Document in `PROGRAMMER_ENTRY.md`:
   ```
   Developer Working Branch: main
   ```

**NOT recommended:**
- Merging entire `runtime-validation-v0.1` (contains validation experiment commits)
- Keeping current HEAD positions (one has unpushed work; the other's repo also has an unmerged quarantine branch sitting alongside it that a new programmer would have to be told about)
- Telling programmer "use runtime-validation-v0.1 for frontend, e266213 for backend" (not one branch)

---

## Verification

After decision, must confirm:
- [ ] Frontend HEAD = `main`
- [ ] Backend HEAD = `main`
- [ ] Neither HEAD is ancestor-linked to `2036bf9` (quarantine remains a separate, unmerged branch)
- [ ] Repository topology doc present in frontend
- [ ] Disposition doc present in backend
- [ ] `git status` shows clean working tree
- [ ] `.env.example` present
- [ ] README.md present in both repos
- [ ] Test command documented and works

---

**Status:** A = preferred candidate（both `main` anchors proven canonical：backend e266213 / frontend faa01d4）  
**B** = isolated integration branch，仅当 governance/staging 无法安全直接落 `main` 时启用
