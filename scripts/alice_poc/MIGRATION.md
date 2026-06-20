# 迁移到另一台 Mac —— Provider Harness Smoke

> **口径**：可以迁移，但不是拷过去就完事。另一台 Mac **必须重新做一次 Provider Harness Smoke**。
> 这套是「Mac Wind Alice Desktop Provider Harness」，**不是跨机器免配置服务**。

`data/*.json`（证据链）没进 git，换机器不会自带历史证据——不影响新跑，新机自己产生证据。

---

## 前置条件（缺一不可）

1. 那台 Mac 装了 **Mac 版 Wind 万得终端**，能登录 **Alice**。
2. Alice Chat 页面能打开，停在 **「金融问答」** 模式。
3. 给**真正执行任务的进程**授权（这条最咬人，见下方"授权对象"）：
   - 系统设置 → 隐私与安全性 → **辅助功能**
   - 系统设置 → 隐私与安全性 → **输入监控**

---

## Smoke 步骤（按顺序，别跳）

```bash
cd /Users/Zhuanz/finance-suite/scripts/alice_poc

# ① 重新编译（二进制没进 git，必须在新机重编）
swiftc -O wind_focus.swift -o wind_focus \
  -framework Cocoa -framework ApplicationServices

# ② 前台焦点（blocker 本体，先单验）—— 失败 exit 3 / 未授权 exit 2
./wind_focus focus

# ③ 几何基准（关键！坐标偏移几乎一定要按新机重校）
./wind_focus geom
#   → 看 INPUT x/y/w/h。若窗口宽 ≠ 1470，三档 x 偏移会偏，
#     需按真实 INPUT frame 调 wind_focus.swift 里 MODE_OFFSETS。

# ④ AX 树（确认输入框 AXTextArea 还在）
./wind_focus tree | grep EDITABLE

# ⑤ 端到端（Swift 一条龙：focus→ensure_mode→type→Cmd+Return）
./wind_focus query "北方华创 最近三个月的核心分歧点是什么？请用两句话回答。" 金融问答

# ⑥ Python runner（加等待+锚点解析+落盘 data/NN.json）
python3 run_alice_poc.py --prompt "北方华创 最近三个月的核心分歧点是什么？请用两句话回答。"
#   → 读 data/ 最新 json：status=success / parse=success / answer 是真回答才算 PASS
```

---

## 新机最容易出问题的三处

### 1. 「金融问答」坐标偏移 —— 几乎必然要重校
三档（金融问答/深度研究/事实核验）在 WebView 内，AX 扫不到，走坐标 fallback，锚输入框 frame + 经验偏移 `(70,-26)`。这偏移是按**原机 1470 宽窗口**估的。新机分辨率/窗口宽一变就偏。
→ **第一件事跑 `./wind_focus geom`**，按真实 INPUT frame 调 `MODE_OFFSETS`。

### 2. 授权对象 = 真正执行的进程（不是你测试时手敲的终端）
- 手动开 iTerm/Terminal 跑 → 授权 **iTerm/Terminal**
- launchd 拉起 → 授权 **launchd 实际执行链路的进程**
- VS Code / Claude Code 拉起 → 授权**对应 App**

⚠️ 24h 无人值守最易踩：白天授权了 iTerm，半夜 launchd 用别的身份跑 → `wind_focus` 直接 `exit 2`（未授权硬失败，不静默）。

### 3. 屏幕锁定 / 休眠会让 AX 点击失效
参 [[reference_incident_20260609_closed]]：Mac Sleep/Hibernate 时 launchd 跑、AX 点击落空，状态看起来像"调度故障"实则是睡眠。
→ 无人值守前必须：禁止睡眠（`caffeinate` 或电源设置）+ 保持登录态 + 固定窗口大小/页面。

---

## 上线阶梯 = 7 Gate（别跳级宣布可用）

```text
Gate 1  ./wind_focus focus                       前台焦点
Gate 2  ./wind_focus geom                         窗口检测 + AX + 几何（重校坐标）
Gate 3  ./wind_focus query "测试问题" 金融问答      prompt 注入 + 提交
Gate 4  python3 run_alice_poc.py --prompt "测试"   capture + 锚点解析 + 落盘 success
Gate 5  2h watch                                  短时稳定性
Gate 6  overnight watch                           过夜：睡眠/登录态/内存/Wind弹窗/网络重连
Gate 7  24h resident                              常驻
```

**先 A（终端常驻 + 手动 smoke）最稳，A 稳了再升 launchd。上线前不要直接无人值守。**

### ⚠️ Geom PASS ≠ Provider PASS（最易被忽略的验证门）
`./wind_focus geom`（Gate 2）只证明 **窗口检测 + Accessibility + UI 几何**。
它**没证明** prompt 注入 + response capture + 长时间稳定性。
→ **真正决定能否恢复 Wind 信源的是 Gate 4 之后**：`Prompt → Alice → Capture → Structured Output` 能否**稳定**跑。
（同构 [[feedback_fallback_endpoint_not_real_data]]：路由可达 ≠ 数据接通。）

---

## 接回 Finance Suite 时的标签（防故障误判）

把它明确标成，**不要和 mock / fallback / api 混**：
```
provider_tier  = desktop
provider_mode  = real
provider_class = wind_alice_harness
```
本质是**真人桌面软件自动化 Provider**，不是 API Provider。

这样当 **Wind 升级 UI / Alice 改版 / Mac 权限重置** 导致故障时，能立刻定位到
**Desktop Harness Layer**，而不会误判成 Research Runtime / Trust Gate / Data Gateway 的问题。
（对应 [[feedback_misclassification_three_layer]]：用户感知 ≠ Route ≠ 基础设施 ≠ Capability。）

---

## 状态归类（最终口径 2026-06-21）

```text
Mac Wind Alice Desktop Provider Harness
Status:             Portable / Not Plug-and-Play
Current Confidence: Lab Verified
Production Status:  Unproven
Provider Tier:      desktop
Provider Mode:      real
Provider Class:     wind_alice_harness
用途:               Wind 信源恢复候选 Provider（Facts Candidate + Beliefs Summary）
不是:               跨机器免配置服务 / WindPy 硬数据源 / API Provider
护栏:               Alice 输出是 AI 生成内容，核查护栏保留
```

### 命名纪律（防提前升级）
现在只能叫 **Lab Verified Desktop Harness**。
**不能**叫 **Production Wind Provider**。
- Gate 4 才证明 `Prompt → Alice → Capture → Structured Output`
- Gate 7（24h Resident PASS）后才能说 **Candidate Real Provider**
- 新机迁移 PASS + Overnight PASS + 24h PASS → 全绿才升 Candidate Real Provider

晋级路径：
```
Lab Verified（现在）
  → New Mac Migration PASS
    → Overnight Stability PASS
      → 24h Resident PASS
        → Candidate Real Provider
```
