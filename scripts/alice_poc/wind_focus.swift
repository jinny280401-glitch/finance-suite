// wind_focus.swift —— Wind 前台焦点 + AX 输入框定位（解决 6/20 真 blocker）
//
// 背景：6/20 用 CoreGraphics 盲发键鼠事件，事件 fire 但落到 Codex 而非 Wind，
//      因为 activate 异步、Wind 没稳定成为 frontmost。坐标/盲发都治不了这个。
//
// 本工具用 Accessibility API（AXUIElement）做三件确定性的事：
//   1. focus    —— 把 Wind 提到前台，并**轮询确认** frontmost == Wind 才返回（不再赌异步）
//   2. tree     —— dump Wind 主窗口的 AX 控件树，人工找 Alice 输入框的 role/标识
//   3. type     —— 不靠坐标：AX 找到第一个可编辑 text 控件，setValue 直接写入 query
//   4. send     —— 写入后对该控件发 AXConfirm（回车），或回退到 CGEvent 回车
//
// 编译：swiftc -O wind_focus.swift -o wind_focus -framework Cocoa -framework ApplicationServices
// 用法：
//   ./wind_focus focus
//   ./wind_focus tree            # 先看树，确认输入框 AX 路径
//   ./wind_focus type "北方华创 最近三个月的核心分歧是什么？"
//   ./wind_focus send            # 单独发回车
//   ./wind_focus query "..."     # focus → type → send 一条龙
//
// 前置：系统设置 → 隐私与安全性 → 辅助功能：勾选运行它的终端/进程。
//      未授权时 AXIsProcessTrusted() 返回 false，本工具会直接报错退出（不会静默假成功）。

import Cocoa
import ApplicationServices

let WIND_BUNDLE_ID = "com.wind.mac.Windotd"

// ---- 辅助功能权限：硬门槛，不通过就退出 ----
func ensureTrusted() {
    if !AXIsProcessTrusted() {
        FileHandle.standardError.write("ERR: accessibility not trusted. 系统设置→隐私与安全性→辅助功能 勾选当前终端。\n".data(using: .utf8)!)
        exit(2)
    }
}

func windApp() -> NSRunningApplication? {
    return NSRunningApplication.runningApplications(withBundleIdentifier: WIND_BUNDLE_ID).first
}

// 把 Wind 提到前台，轮询确认 frontmost 真的是 Wind 才返回 true
@discardableResult
func focusWind(timeout: Double = 3.0) -> Bool {
    guard let app = windApp() else {
        FileHandle.standardError.write("ERR: Wind not running (\(WIND_BUNDLE_ID))\n".data(using: .utf8)!)
        return false
    }
    // macOS 14+：activateIgnoringOtherApps 已失效。先 unhide 再 activate，
    // 并显式把主窗口 raise（AX）双保险。
    app.unhide()
    if #available(macOS 14.0, *) {
        app.activate()
    } else {
        app.activate(options: [.activateIgnoringOtherApps])
    }
    // AX 层再 raise 一次主窗口，对付 activate 不抢焦的情况
    let axEl = AXUIElementCreateApplication(app.processIdentifier)
    if let w = mainWindow(axEl) {
        AXUIElementPerformAction(w, kAXRaiseAction as CFString)
    }
    let deadline = Date().addingTimeInterval(timeout)
    while Date() < deadline {
        if let front = NSWorkspace.shared.frontmostApplication,
           front.bundleIdentifier == WIND_BUNDLE_ID {
            // 再给窗口服务器一拍稳定时间
            usleep(150_000)
            return true
        }
        usleep(80_000)
    }
    FileHandle.standardError.write("ERR: Wind did not become frontmost within \(timeout)s (focus ownership lost — 这正是旧 blocker)\n".data(using: .utf8)!)
    return false
}

func axApp() -> AXUIElement? {
    guard let app = windApp() else { return nil }
    return AXUIElementCreateApplication(app.processIdentifier)
}

func copyAttr(_ el: AXUIElement, _ attr: String) -> AnyObject? {
    var v: AnyObject?
    let err = AXUIElementCopyAttributeValue(el, attr as CFString, &v)
    return err == .success ? v : nil
}

func children(_ el: AXUIElement) -> [AXUIElement] {
    guard let arr = copyAttr(el, kAXChildrenAttribute as String) as? [AXUIElement] else { return [] }
    return arr
}

func role(_ el: AXUIElement) -> String { (copyAttr(el, kAXRoleAttribute as String) as? String) ?? "?" }
func subrole(_ el: AXUIElement) -> String { (copyAttr(el, kAXSubroleAttribute as String) as? String) ?? "" }

// dump AX 树（限深度，避免爆栈）
func dumpTree(_ el: AXUIElement, depth: Int, maxDepth: Int) {
    let indent = String(repeating: "  ", count: depth)
    let r = role(el)
    let sr = subrole(el)
    let title = (copyAttr(el, kAXTitleAttribute as String) as? String) ?? ""
    let desc = (copyAttr(el, kAXDescriptionAttribute as String) as? String) ?? ""
    let val = (copyAttr(el, kAXValueAttribute as String) as? String) ?? ""
    var settable = DarwinBoolean(false)
    AXUIElementIsAttributeSettable(el, kAXValueAttribute as CFString, &settable)
    let editable = settable.boolValue ? " [EDITABLE]" : ""
    let shortVal = val.count > 40 ? String(val.prefix(40)) + "…" : val
    let frameText: String
    if let f = axFrame(el) {
        frameText = " frame=(\(Int(f.minX)),\(Int(f.minY)),\(Int(f.width)),\(Int(f.height)))"
    } else {
        frameText = ""
    }
    print("\(indent)\(r)\(sr.isEmpty ? "" : "/\(sr)")\(editable)\(frameText) title=\"\(title)\" desc=\"\(desc)\" val=\"\(shortVal)\"")
    if depth < maxDepth {
        for c in children(el) { dumpTree(c, depth: depth + 1, maxDepth: maxDepth) }
    }
}

// 深度优先找第一个「可写入的文本控件」：AXTextField / AXTextArea，且 value 可 set
func findEditable(_ el: AXUIElement, depth: Int = 0) -> AXUIElement? {
    let r = role(el)
    if r == "AXTextField" || r == "AXTextArea" {
        var settable = DarwinBoolean(false)
        AXUIElementIsAttributeSettable(el, kAXValueAttribute as CFString, &settable)
        if settable.boolValue { return el }
    }
    if depth > 40 { return nil }
    for c in children(el) {
        if let hit = findEditable(c, depth: depth + 1) { return hit }
    }
    return nil
}

// ---- 回答模式档（输入框上方三档：金融问答 / 深度研究 / 事实核验）----
// 截图实证（2026-06-20）：UI 有两层，别混。
//   顶层导航：Search/Chat/Writer/Reader/Meeting/Advisor/...（大功能 tab，不是这里要的）
//   输入框上方：[金融问答][深度研究][事实核验]（圆角胶囊，role 很可能是 AXButton）
// ensure_mode 只认「这三档之一」，且**只在输入框那排里找**，避免误点顶层大 tab。
// 选中态属性未知（金融问答高亮）→ 先按 AXValue/AXSelected 试，跑 tree 确认后再收紧。

// 已知的三档模式名（白名单）。匹配时要求 title 命中其一，杜绝抓到顶部 8 个大 tab。
let MODE_NAMES = ["金融问答", "深度研究", "事实核验"]

func looksLikeModeChip(_ el: AXUIElement) -> Bool {
    let r = role(el)
    // 胶囊按钮通常 AXButton；保留 AXRadioButton 兜底
    guard r == "AXButton" || r == "AXRadioButton" || r == "AXCheckBox" else { return false }
    let t = tabTitle(el)
    return MODE_NAMES.contains { t.contains($0) || $0.contains(t) && !t.isEmpty }
}

func tabTitle(_ el: AXUIElement) -> String {
    let t = (copyAttr(el, kAXTitleAttribute as String) as? String) ?? ""
    if !t.isEmpty { return t }
    // 有些 tab 文字在 AXDescription 或子 AXStaticText 里
    let d = (copyAttr(el, kAXDescriptionAttribute as String) as? String) ?? ""
    if !d.isEmpty { return d }
    for c in children(el) {
        if role(c) == "AXStaticText" {
            let v = (copyAttr(c, kAXValueAttribute as String) as? String) ?? ""
            if !v.isEmpty { return v }
        }
    }
    return ""
}

func tabSelected(_ el: AXUIElement) -> Bool {
    if let v = copyAttr(el, kAXValueAttribute as String) {
        if let n = v as? Int { return n != 0 }
        if let b = v as? Bool { return b }
    }
    // AXTab 用 AXSelected
    if let s = copyAttr(el, "AXSelected") as? Bool { return s }
    return false
}

// 只收集「三档模式 chip」，白名单隔离 —— 不会抓到顶部 8 个大功能 tab
func collectModeChips(_ el: AXUIElement, _ acc: inout [AXUIElement], depth: Int = 0) {
    if depth > 40 { return }
    if looksLikeModeChip(el) { acc.append(el) }
    for c in children(el) { collectModeChips(c, &acc, depth: depth + 1) }
}

// 确保切到目标模式。exit 语义：0=已在目标/已点中，6=未找到匹配 chip（会列出候选）
func ensureMode(_ want: String) -> Int32 {
    guard let app = axApp(), let win = mainWindow(app) else {
        FileHandle.standardError.write("ERR: no AX window\n".data(using: .utf8)!); return 4
    }
    var chips: [AXUIElement] = []
    collectModeChips(win, &chips)
    if chips.isEmpty {
        // C 已确认：三档在 WebView，AX 扫不到 → 自动回退坐标点击（锚输入框 frame）
        FileHandle.standardError.write(
            "INFO: AX 扫不到三档 chip（WebView，已知情况）→ 回退坐标点击。\n".data(using: .utf8)!)
        return clickMode(want)
    }
    // 第一次跑必看：列出三档真实 title / role / 选中态
    FileHandle.standardError.write("MODE CHIPS:\n".data(using: .utf8)!)
    for c in chips {
        let line = "  - \"\(tabTitle(c))\" role=\(role(c)) selected=\(tabSelected(c))\n"
        FileHandle.standardError.write(line.data(using: .utf8)!)
    }
    let hit = chips.first { c in
        let t = tabTitle(c)
        return !t.isEmpty && (t.contains(want) || want.contains(t))
    }
    guard let target = hit else {
        FileHandle.standardError.write("ERR: 没有 chip 的 title 匹配 \"\(want)\"。看上面 MODE CHIPS，用真实 title 重跑。\n".data(using: .utf8)!)
        return 6
    }
    if tabSelected(target) {
        FileHandle.standardError.write("OK: 已在「\(want)」模式，无需切换。\n".data(using: .utf8)!)
        return 0
    }
    let e = AXUIElementPerformAction(target, kAXPressAction as CFString)
    if e != .success {
        AXUIElementSetAttributeValue(target, kAXValueAttribute as CFString, kCFBooleanTrue)
    }
    usleep(200_000)
    FileHandle.standardError.write("OK: 已点击切到「\(want)」。\n".data(using: .utf8)!)
    return 0
}

func mainWindow(_ app: AXUIElement) -> AXUIElement? {
    if let w = copyAttr(app, kAXMainWindowAttribute as String) { return (w as! AXUIElement) }
    if let ws = copyAttr(app, kAXWindowsAttribute as String) as? [AXUIElement], let f = ws.first { return f }
    return nil
}

// 把文本写进输入框。不要只用 AX setValue：WebView/React 可能显示了文本，
// 但内部 input 状态没触发，导致发送按钮点了也不提交。这里改为聚焦控件后
// 通过剪贴板 Cmd+A/Cmd+V 粘贴，让前端收到真实输入事件。
func typeIntoAlice(_ text: String) -> AXUIElement? {
    guard let app = axApp(), let win = mainWindow(app) else {
        FileHandle.standardError.write("ERR: no AX window\n".data(using: .utf8)!); return nil
    }
    guard let field = findEditable(win) else {
        FileHandle.standardError.write("ERR: no editable text control found (跑 `tree` 看结构，可能是 WebView 内控件需另寻 role)\n".data(using: .utf8)!)
        return nil
    }
    // 先聚焦该控件
    AXUIElementSetAttributeValue(field, kAXFocusedAttribute as CFString, kCFBooleanTrue)
    usleep(120_000)

    let pb = NSPasteboard.general
    pb.clearContents()
    pb.setString(text, forType: .string)

    // 清空旧输入并粘贴新文本。keycode: A=0, V=9。
    sendCmdKey(0)
    usleep(80_000)
    sendCmdKey(9)
    usleep(180_000)
    return field
}

// 点击输入框右下角发送按钮。截图实证：Alice 更可靠的提交入口是这个按钮，
// Return/AXConfirm 有时只写入不提交。
func clickSendButton(_ field: AXUIElement?) -> Bool {
    guard let app = axApp(), let win = mainWindow(app), let wf = axFrame(win) else { return false }
    // 发送按钮在 Wind 窗口右下角，AX 通常暴露成无语义小图标，而不是 TextArea 子节点。
    let p = sendCandidatePoint(win, in: wf) ?? CGPoint(x: wf.maxX - 76, y: wf.maxY - 39)
    FileHandle.standardError.write("CLICK send @ (\(Int(p.x)),\(Int(p.y))) [window x=\(Int(wf.minX)) y=\(Int(wf.minY)) w=\(Int(wf.width)) h=\(Int(wf.height))]\n".data(using: .utf8)!)
    clickAt(p)
    usleep(250_000)
    return true
}

// 发送：使用 Alice Chat 实测可靠的 Cmd+Return。
func sendReturn(_ field: AXUIElement?) {
    // 实测 Alice Chat 的可靠提交键是 Cmd+Return；普通 Return 只会停在输入框。
    // 右下角发送图标在不同窗口状态下会和 Wind/Cosmos 底栏重叠，暂不走坐标。
    sendCmdKey(36)
}

// ---- 坐标 fallback（C：三档在 WebView 内，AX 不暴露，只能点）----
// 纪律：不盲点屏幕绝对坐标。以「输入框 AXTextArea 的 AX frame」为锚，
//       三档恒在输入框正上方同一排 → 用相对偏移算点击点，窗口移动也不崩。

// 取控件 frame（屏幕坐标，原点左上）。失败返回 nil。
func axFrame(_ el: AXUIElement) -> CGRect? {
    var posV: AnyObject?
    var sizeV: AnyObject?
    guard AXUIElementCopyAttributeValue(el, kAXPositionAttribute as CFString, &posV) == .success,
          AXUIElementCopyAttributeValue(el, kAXSizeAttribute as CFString, &sizeV) == .success
    else { return nil }
    var pos = CGPoint.zero
    var size = CGSize.zero
    AXValueGetValue(posV as! AXValue, .cgPoint, &pos)
    AXValueGetValue(sizeV as! AXValue, .cgSize, &size)
    return CGRect(origin: pos, size: size)
}

// 找输入框（复用 findEditable）并返回其 frame
func inputFrame() -> CGRect? {
    guard let app = axApp(), let win = mainWindow(app), let field = findEditable(win) else { return nil }
    return axFrame(field)
}

// 打印窗口 + 输入框 frame，用于定坐标基准
func dumpGeom() -> Int32 {
    guard let app = axApp(), let win = mainWindow(app) else { print("no window"); return 4 }
    if let wf = axFrame(win) {
        print("WINDOW  x=\(Int(wf.minX)) y=\(Int(wf.minY)) w=\(Int(wf.width)) h=\(Int(wf.height))")
    }
    if let f = inputFrame() {
        print("INPUT   x=\(Int(f.minX)) y=\(Int(f.minY)) w=\(Int(f.width)) h=\(Int(f.height))")
        // 三档预测点（输入框上沿往上 ~26px 那一排，左起依次排）。比例先给经验值，clickmode 用得到。
        let rowY = f.minY - 26
        let x1 = f.minX + 70     // 金融问答
        let x2 = f.minX + 190    // 深度研究
        let x3 = f.minX + 300    // 事实核验
        print("PREDICT row_y=\(Int(rowY))  金融问答≈(\(Int(x1)),\(Int(rowY)))  深度研究≈(\(Int(x2)),\(Int(rowY)))  事实核验≈(\(Int(x3)),\(Int(rowY)))")
        print("NOTE 这些是经验偏移，clickmode 前请按截图核对；偏移可在源码 MODE_OFFSETS 调。")
    } else {
        print("no input frame — findEditable 没命中，坐标 fallback 也无锚点")
        return 5
    }
    return 0
}

// 三档相对输入框左上角的 (dx, dy) 偏移。dy 为负=在输入框上方。
// ⚠️ 经验值，需用 geom + 截图核对后定稿。
let MODE_OFFSETS: [String: (CGFloat, CGFloat)] = [
    "金融问答": (70, -26),
    "深度研究": (190, -26),
    "事实核验": (300, -26),
]

// CGEvent 在指定屏幕坐标点击（Wind 已 frontmost 才调）
func clickAt(_ p: CGPoint) {
    let src = CGEventSource(stateID: .hidSystemState)
    let down = CGEvent(mouseEventSource: src, mouseType: .leftMouseDown, mouseCursorPosition: p, mouseButton: .left)
    let up = CGEvent(mouseEventSource: src, mouseType: .leftMouseUp, mouseCursorPosition: p, mouseButton: .left)
    down?.post(tap: .cghidEventTap)
    usleep(40_000)
    up?.post(tap: .cghidEventTap)
}

func sendCandidatePoint(_ el: AXUIElement, in windowFrame: CGRect, depth: Int = 0) -> CGPoint? {
    if depth > 80 { return nil }
    var best: (score: CGFloat, point: CGPoint)?

    let r = role(el)
    if (r == "AXImage" || r == "AXButton" || r == "AXGroup" || r == "AXEmptyGroup"),
       let f = axFrame(el),
       f.width >= 8, f.width <= 80,
       f.height >= 8, f.height <= 80,
       f.midX > windowFrame.maxX - 180,
       f.midX < windowFrame.maxX - 30,
       f.midY > windowFrame.maxY - 100,
       f.midY < windowFrame.maxY - 20 {
        let p = CGPoint(x: f.midX, y: f.midY)
        best = (p.x + p.y, p)
    }

    for c in children(el) {
        if let p = sendCandidatePoint(c, in: windowFrame, depth: depth + 1) {
            let score = p.x + p.y
            if best == nil || score > best!.score {
                best = (score, p)
            }
        }
    }
    return best?.point
}

// 坐标点击某一档模式。返回 0=点了，5=无锚点，1=未知档名
func clickMode(_ want: String) -> Int32 {
    guard let off = MODE_OFFSETS[want] else {
        FileHandle.standardError.write("ERR: 未知档名 \"\(want)\"（金融问答/深度研究/事实核验）\n".data(using: .utf8)!)
        return 1
    }
    guard let f = inputFrame() else {
        FileHandle.standardError.write("ERR: 无输入框锚点，坐标 fallback 失败\n".data(using: .utf8)!)
        return 5
    }
    let p = CGPoint(x: f.minX + off.0, y: f.minY + off.1)
    FileHandle.standardError.write("CLICK 「\(want)」@ (\(Int(p.x)),\(Int(p.y)))  [anchor input x=\(Int(f.minX)) y=\(Int(f.minY))]\n".data(using: .utf8)!)
    clickAt(p)
    usleep(200_000)
    return 0
}

// ---- capture：focus + AX 文本导出，吐到 stdout（纯文本）----
// 隔离验证抓取段用。不要再走 Cmd+A/C：实测 focus 可成功，但键盘复制仍可能落回 Codex。
// 这里直接遍历 Wind 主窗口 AX 树，按视觉/DOM 顺序收集 title/desc/value 文本。
// 切回答靠 Python 端的锚点（分享 / 内容由AI生成）。

func sendCmdKey(_ key: CGKeyCode) {
    let src = CGEventSource(stateID: .hidSystemState)
    let down = CGEvent(keyboardEventSource: src, virtualKey: key, keyDown: true)
    down?.flags = .maskCommand
    let up = CGEvent(keyboardEventSource: src, virtualKey: key, keyDown: false)
    up?.flags = .maskCommand
    down?.post(tap: .cghidEventTap)
    usleep(30_000)
    up?.post(tap: .cghidEventTap)
}

func appendTextAttr(_ el: AXUIElement, _ attr: String, _ out: inout [String]) {
    guard let s = copyAttr(el, attr) as? String else { return }
    let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
    if t.isEmpty { return }
    if out.last == t { return }
    out.append(t)
}

func collectAXText(_ el: AXUIElement, depth: Int = 0, out: inout [String]) {
    if depth > 80 { return }
    appendTextAttr(el, kAXTitleAttribute as String, &out)
    appendTextAttr(el, kAXDescriptionAttribute as String, &out)
    appendTextAttr(el, kAXValueAttribute as String, &out)
    for c in children(el) {
        collectAXText(c, depth: depth + 1, out: &out)
    }
}

func captureText() -> Int32 {
    guard focusWind(timeout: 3.0) else { return 3 }
    guard let app = axApp(), let win = mainWindow(app) else {
        FileHandle.standardError.write("ERR: no Wind main window\n".data(using: .utf8)!)
        return 4
    }
    var lines: [String] = []
    collectAXText(win, out: &lines)
    let txt = lines.joined(separator: "\n")
    FileHandle.standardOutput.write(txt.data(using: .utf8) ?? Data())
    if txt.isEmpty {
        FileHandle.standardError.write("WARN: AX 文本为空（页面可能未加载或 AX 不暴露文本）\n".data(using: .utf8)!)
        return 7
    }
    FileHandle.standardError.write("OK: captured \(txt.count) chars via AX text\n".data(using: .utf8)!)
    return 0
}

// ---- main ----
let args = CommandLine.arguments
guard args.count >= 2 else {
    print("usage: wind_focus <focus|tree|geom|capture|mode MODE|clickmode MODE|type TEXT|send|query TEXT [MODE]>")
    exit(1)
}
ensureTrusted()
let cmd = args[1]
switch cmd {
case "focus":
    exit(focusWind() ? 0 : 3)
case "tree":
    guard focusWind() else { exit(3) }
    guard let app = axApp(), let win = mainWindow(app) else { print("no window"); exit(4) }
    dumpTree(win, depth: 0, maxDepth: 12)
case "mode":
    guard args.count >= 3 else { print("mode needs MODE name, e.g. 金融问答"); exit(1) }
    guard focusWind() else { exit(3) }
    exit(ensureMode(args[2]))   // AX 优先，扫不到自动回退坐标
case "geom":
    guard focusWind() else { exit(3) }
    exit(dumpGeom())            // 打印窗口/输入框 frame + 三档预测点，用于核对偏移
case "capture":
    exit(captureText())         // focus+AX文本遍历 → 全页文本到 stdout（隔离验证抓取段）
case "clickmode":
    guard args.count >= 3 else { print("clickmode needs MODE name"); exit(1) }
    guard focusWind() else { exit(3) }
    exit(clickMode(args[2]))    // 直接坐标点击某档（绕过 AX）
case "type":
    guard args.count >= 3 else { print("type needs TEXT"); exit(1) }
    guard focusWind() else { exit(3) }
    let f = typeIntoAlice(args[2])
    exit(f == nil ? 5 : 0)
case "send":
    guard focusWind() else { exit(3) }
    sendReturn(nil)
case "query":
    // query TEXT [MODE]：给了 MODE 就先 ensure_mode（满足 ensure_mode("金融问答") 需求）
    guard args.count >= 3 else { print("query needs TEXT"); exit(1) }
    guard focusWind() else { exit(3) }
    if args.count >= 4 {
        let mc = ensureMode(args[3])
        if mc != 0 {
            FileHandle.standardError.write("WARN: ensure_mode 未命中，继续在当前模式发送（mode_guard=unknown）\n".data(using: .utf8)!)
        }
    }
    guard let f = typeIntoAlice(args[2]) else { exit(5) }
    usleep(250_000)
    sendReturn(f)
default:
    print("unknown cmd: \(cmd)"); exit(1)
}
