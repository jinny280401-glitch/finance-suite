# Wind Alice PoC

把 Wind 终端内置的 **Alice** AI 助手当作 Finance Suite 的「观点增强源」（机构视角 / 研报摘要 / AI 观点），
**不替代** WindPy / Tushare / JoinQuant / AkShare 的结构化硬数据。Alice 的回答标 `data_class: ai_generated_opinion`，不可用于硬指标计算。

---

## 文件清单

| 文件 | 作用 | 状态 |
|---|---|---|
| `wind_focus.swift` / `wind_focus` | **AX 前台控制器**（焦点 + 输入框定位 + 回车）。解决前台焦点 blocker。 | 已编译 ✅ |
| `run_alice_poc.py` | **v2 runner**：AX 控制 + 锚点解析。当前主用。 | 语法验证 ✅，未实跑 |
| `run_alice_poc.RECOVERED.py` | 从 `.pyc` 反汇编恢复的 **5/10 基线**，带已知缺陷，仅作对照。 | 可跑（带坑） |
| `prompts.txt` | 10 条验收问题，第 1 条 = 北方华创 smoke。 | ✅ |
| `data/` | 每条结果一个 `NN.json`。 | 运行时生成 |
| `__pycache__/run_alice_poc.cpython-312.pyc` | 唯一幸存的旧编译产物（恢复来源，勿删）。 | — |

---

## 这次为什么重做控制端（根因）

**6/20 实测**：用 CoreGraphics 盲发键鼠事件，事件 fire 成功，但落到了 Codex 输入框而非 Wind ——
`activate` 是**异步**的，发完不等窗口到前台就发键，焦点还在原 app。坐标/盲发都治不了这个。

**旧 `.pyc` 的价值在解析端，不在控制端**：它的 `activate_wind → keystroke` 是同一个坑，
只是 5/10 靠「手动先点好输入框」绕过了，从没真正解决。而且它的 `extract_last_answer` 用 `\n\n` 切段，
**没用 memory 里记的锚点** —— 这是 5/10 抓取为空的另一半原因。

→ 控制端整个换成 **AX（Accessibility API）**，解析端换成 **锚点**。

---

## 关键事实（5/10 确认 + 6/20 补充）

- bundle id：`com.wind.mac.Windotd`（进程名 `Wind` 与 Wind API.app 撞名，**必须按 bundle id 激活**）
- 发送键：**回车 = 发送**（非 Shift+Enter）
- 剪贴板锚点（5/10 手动验证）：
  - 开始：`"分享"` 之后是对话区
  - 结束：`"内容由AI生成，请核查重要信息"` 之前是对话区
  - 中间按 `\n\n` 切，倒数第一段 = 最新 Alice 回答
- Wind 没有 URL scheme 直达 Alice（查过 Info.plist + LaunchServices：只有 `orpheus:` / `baiduyunguanjia:` 等无关 scheme，无 alice/achat）。二进制里有 `htdocs/alice/` 路径但那是内部 WebView 资源，非可调度入口。
- 本机无 cliclick / Hammerspoon / Keyboard Maestro / pyobjc → 故走 Swift 原生 AX。

---

## 用法

### 0. 编译控制器（一次）
```bash
cd /Users/Zhuanz/finance-suite/scripts/alice_poc
swiftc -O wind_focus.swift -o wind_focus -framework Cocoa -framework ApplicationServices
```

### 1. 授权（一次）
系统设置 → 隐私与安全性 → 辅助功能 → 勾选运行它的终端（iTerm / Terminal / Warp）。
未授权时 `wind_focus` 以 `exit 2` 报错，**不会静默假成功**。

### 2. 先验证前台控制（不发 query，最安全的第一步）
```bash
./wind_focus focus     # Wind 提到前台并确认 frontmost == Wind；失败 exit 3
./wind_focus tree      # dump Alice 窗口 AX 控件树 → 确认输入框的 role/标识
```
> `tree` 输出里找带 `[EDITABLE]` 的 `AXTextField`/`AXTextArea`，那就是 `type` 会写入的目标。
> 若输入框在 WebView 里（role 可能是 `AXTextArea` 或 web 专有 role），按实际输出调 `findEditable`。

### 3. Alice Harness Smoke Test（北方华创）
```bash
# 纯 Swift 一条龙（focus → setValue → 回车），最干净
./wind_focus query "北方华创 最近三个月的核心分歧点是什么？"

# 或走 Python（含等待 + 锚点解析 + 落盘 data/NN.json）
python3 run_alice_poc.py --prompt "北方华创 最近三个月的核心分歧点是什么？"
```

### 4. 看 prompts / 批量
```bash
python3 run_alice_poc.py --dry-run
python3 run_alice_poc.py --batch
```

---

## 建议执行顺序（给审代码的人）

1. `./wind_focus focus` —— 前台焦点能不能稳定拿到（这是 blocker 本体，先验证它）
2. `./wind_focus tree` —— 输入框 AX 路径对不对（决定 `type` 能否命中）
3. `./wind_focus query "北方华创…"` —— 端到端发送
4. `python3 run_alice_poc.py --prompt "北方华创…"` —— 加上等待 + 锚点解析 + 落盘
5. 读 `data/01.json` 的 `parse_status` / `answer` —— 锚点切得准不准

**只跑 smoke，不动 Deep Research / Runtime。**

---

## 边界（用户确认过）

不抓包、不逆向、不破解 token；不自动登录；不自动处理弹窗；不做 24 小时挂机；
Alice 回答不当结构化数据，只当观点增强源。
