#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wind Alice PoC runner（v2 —— AX 前台控制 + 锚点解析）

与恢复基线（run_alice_poc.RECOVERED.py）的差异 —— 只动两端，不动 QC/落盘契约：

  发送/控制端：弃用 osascript `activate → keystroke`（异步、焦点不保证，6/20 实测事件落到 Codex）。
              改调 ./wind_focus（Swift + Accessibility API）：
                - focusWind 轮询确认 Wind 真的 frontmost 才动作
                - 输入框靠 AX 控件定位 + setValue，不靠坐标
  解析端：弃用「\n\n 切段取最后一段」。改用 memory 里 5/10 手动验证过的锚点：
                - 开始锚点 "分享" 之后
                - 结束锚点 "内容由AI生成，请核查重要信息" 之前
                - 中间按 \n\n 切，取倒数第一段
          锚点缺失时回退到 RECOVERED 的旧启发式（不丢原文）。

前置：
  1. swiftc -O wind_focus.swift -o wind_focus -framework Cocoa -framework ApplicationServices
  2. Wind 已登录、Alice Chat 已打开
  3. 终端有「辅助功能」权限（wind_focus 未授权会以 exit 2 报错，不会静默假成功）

用法同 v1：
  python3 run_alice_poc.py --prompt "北方华创 最近三个月核心分歧是什么？"
  python3 run_alice_poc.py --index 3
  python3 run_alice_poc.py --batch
  python3 run_alice_poc.py --dry-run
"""

import argparse
import json
import os
import subprocess
import time

WIND_BUNDLE_ID = "com.wind.mac.Windotd"
VERSION = "25.4.1"
HERE = os.path.dirname(os.path.abspath(__file__))
FOCUS_BIN = os.path.join(HERE, "wind_focus")

# 5/10 手动验证过的剪贴板锚点
ANCHOR_START = "分享"
ANCHOR_END = "内容由AI生成，请核查重要信息"


# ---------- 剪贴板 ----------

def set_clipboard(text):
    subprocess.run(["pbcopy"], input=text, text=True)


def get_clipboard():
    # The clipboard can contain rich/binary payloads from Wind/WebView. Prefer
    # plain text and decode defensively so a non-text pasteboard item never
    # turns a successful Alice run into a Python UnicodeDecodeError.
    r = subprocess.run(["pbpaste", "-Prefer", "txt"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


# ---------- AX 前台控制（走 Swift 二进制）----------

def _focus(cmd, *extra):
    """调 wind_focus；返回 (ok, stderr)。二进制缺失/未授权都显式失败，不静默。"""
    if not os.path.exists(FOCUS_BIN):
        return (False, "wind_focus 未编译：swiftc -O wind_focus.swift -o wind_focus "
                       "-framework Cocoa -framework ApplicationServices")
    r = subprocess.run([FOCUS_BIN, cmd, *extra], capture_output=True)
    stderr = r.stderr.decode("utf-8", errors="replace").strip()
    stdout = r.stdout.decode("utf-8", errors="replace").strip()
    return (r.returncode == 0, stderr or stdout)


def focus_wind():
    return _focus("focus")


def send_prompt(prompt):
    """AX 一条龙：focus → 输入框 setValue → 回车。失败抛异常，run_one 记 error。"""
    ok, err = _focus("query", prompt, "金融问答")
    if not ok:
        raise RuntimeError("wind_focus query 失败: " + (err or "unknown"))


# ---------- 等待 ----------

def capture_clipboard_once():
    """读取当前 Alice 页全文。读取端不再走 Cmd+A/C；Swift 侧用 AX 树导出文本。"""
    if not os.path.exists(FOCUS_BIN):
        raise RuntimeError("wind_focus 未编译")
    r = subprocess.run([FOCUS_BIN, "capture"], capture_output=True)
    stdout = r.stdout.decode("utf-8", errors="replace")
    stderr = r.stderr.decode("utf-8", errors="replace").strip()
    if r.returncode != 0:
        raise RuntimeError("wind_focus capture 失败: " + (stderr or "unknown"))
    return stdout


def wait_for_answer(min_wait, max_wait, stable_window, poll_interval):
    """剪贴板长度连续 stable_window 秒不变视为完成。返回 (raw_text, elapsed, timed_out)。"""
    t0 = time.time()
    time.sleep(min_wait)
    last_len = -1
    stable_since = None
    last_text = ""
    while True:
        elapsed = time.time() - t0
        if elapsed > max_wait:
            return (last_text, elapsed, True)
        text = capture_clipboard_once()
        cur_len = len(text)
        if cur_len == last_len and cur_len > 0:
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since >= stable_window:
                return (text, time.time() - t0, False)
        else:
            stable_since = None
            last_len = cur_len
            last_text = text
        time.sleep(poll_interval)


# ---------- 解析（锚点版，回退旧启发式）----------

def extract_last_answer(raw_text, prompt):
    """
    锚点优先：截 ANCHOR_START 之后、ANCHOR_END 之前，按 \n\n 取倒数第一非空段。
    锚点缺失回退 RECOVERED 的 \n\n 启发式。返回 (answer, parse_status)。
    """
    text = (raw_text or "").strip()
    if not text:
        return ("", "failed")

    def is_toolbar_noise(s):
        toolbar_markers = ["paper-clip", "金融问答", "深度研究", "事实核验", "创建技能", "使用技能"]
        return len(s.strip()) < 120 and sum(1 for m in toolbar_markers if m in s) >= 3

    # --- prompt 路径：AX 文本抓的是整页，页面可能包含多轮问答/推荐技能。
    # 先用本次 prompt 定位该轮回答，再用 Alice/Wind 元信息作为结束锚点。
    prompt_text = (prompt or "").strip()
    if prompt_text:
        prompt_pos = raw_text.find(prompt_text)
        if prompt_pos != -1:
            body = raw_text[prompt_pos + len(prompt_text):]

            # Alice 的“思考与执行过程”会在最终答案前；看到工具完成标记后再进入正文。
            tool_done = body.find("check-circle eye")
            if 0 <= tool_done < 2000:
                body = body[tool_done + len("check-circle eye"):]

            stop_candidates = []
            for marker in [
                "\nWind数据库",
                "\n文本资料检索",
                "\n本次回答参考",
                "\neye\ncopy",
                "\ncopy\nlike",
                "\n试一试：",
                ANCHOR_END,
            ]:
                pos = body.find(marker)
                if pos != -1:
                    stop_candidates.append(pos)

            # 同一页后面可能出现下一轮同 prompt 或残留复制文本，作为兜底结束锚点。
            next_prompt = body.find(prompt_text)
            if next_prompt > 200:
                stop_candidates.append(next_prompt)

            if stop_candidates:
                body = body[:min(stop_candidates)]

            answer = body.strip()
            if is_toolbar_noise(answer):
                return (answer, "failed")
            if len(answer) >= 50:
                return (answer, "success")
            if len(answer) >= 20:
                return (answer, "partial")

    # --- 锚点路径 ---
    s = raw_text.find(ANCHOR_START)
    e = raw_text.find(ANCHOR_END)
    if s != -1:
        body = raw_text[s + len(ANCHOR_START):]
        if e != -1 and e > s:
            body = raw_text[s + len(ANCHOR_START):e]
        parts = [p.strip() for p in body.split("\n\n") if p.strip()]
        if parts:
            last = parts[-1]
            if len(last) >= 50:
                return (last, "success")
            if len(last) >= 20:
                return (last, "partial")
        # 锚点在但切不出像样段落 → 落回原文，标 partial
        return (raw_text, "partial")

    # --- 回退：RECOVERED 旧逻辑 ---
    if text == prompt.strip() or len(text) < 20:
        return (raw_text, "failed")
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(parts) >= 2:
        last = parts[-1]
        if len(last) >= 50:
            return (last, "success")
        return (raw_text, "partial")
    return (raw_text, "partial")


# ---------- QC / 落盘（与 RECOVERED 契约一致）----------

def build_qc(status, answer, response_time_sec, capture_quality, parse_status, error):
    qc = {
        "source": "wind_alice",
        "provider": "Wind.app " + VERSION,
        "method": "ui_automation_ax",          # 标注：已升级到 AX 控制
        "capture_quality": capture_quality,
        "data_class": "ai_generated_opinion",
        "disclaimer": "AI 生成观点，非 WindPy 原始结构化数据，不可用于硬指标计算",
        "status": status,
        "parse_status": parse_status,
        "response_time_sec": response_time_sec,
        "anchors_used": [ANCHOR_START, ANCHOR_END],
    }
    if error:
        qc["error"] = error
    return qc


def load_prompts(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                out.append(s)
    return out


def next_seq(out_dir):
    import glob
    return len(glob.glob(os.path.join(out_dir, "*.json"))) + 1


def save_result(out_dir, seq, prompt, raw_text, answer, qc):
    payload = {
        "source": "wind_alice",
        "data_class": "ai_generated_opinion",
        "seq": seq,
        "prompt": prompt,
        "answer": answer,
        "raw_clipboard": raw_text,
        "answer_length": len(answer),
        "response_time_sec": qc.get("response_time_sec"),
        "qc": qc,
    }
    path = os.path.join(out_dir, format(seq, "02d") + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def run_one(prompt, seq, out_dir, min_wait, max_wait, stable_window, poll_interval):
    t_start = time.time()
    raw_text, answer, parse_status, error = "", "", "", None
    try:
        send_prompt(prompt)
        raw_text, _, timed_out = wait_for_answer(min_wait, max_wait, stable_window, poll_interval)
        if timed_out:
            status = "timeout"
        elif not raw_text.strip():
            status = "empty"
        else:
            answer, parse_status = extract_last_answer(raw_text, prompt)
            status = "success" if parse_status in ("success", "partial") else "failed"
    except Exception as e:
        status, error = "error", str(e)
        print("  ERROR: " + error)
    elapsed = time.time() - t_start
    qc = build_qc(status, answer, elapsed, "low", parse_status, error)
    path = save_result(out_dir, seq, prompt, raw_text, answer, qc)
    print("  status=" + status + " parse=" + str(parse_status)
          + " raw=" + str(len(raw_text)) + " ans=" + str(len(answer))
          + " time=" + format(elapsed, ".1f") + "s → " + path)
    return qc


def countdown(sec):
    for i in range(sec, 0, -1):
        print("  " + str(i) + " ...", end="\r")
        time.sleep(1)
    print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", help="直接指定一条 prompt")
    p.add_argument("--index", type=int, help="从 prompts.txt 取第 N 条（1-based）")
    p.add_argument("--batch", action="store_true", help="批量跑 prompts.txt 全部")
    p.add_argument("--dry-run", action="store_true", help="只打印 prompt 列表")
    p.add_argument("--prompts", default="prompts.txt")
    p.add_argument("--min-wait", type=float, default=8.0)
    p.add_argument("--max-wait", type=float, default=90.0)
    p.add_argument("--stable-window", type=float, default=3.0)
    p.add_argument("--poll-interval", type=float, default=2.0)
    p.add_argument("--gap-between", type=float, default=5.0)
    args = p.parse_args()

    prompts_path = args.prompts if os.path.isabs(args.prompts) else os.path.join(HERE, args.prompts)
    prompts = load_prompts(prompts_path) if os.path.exists(prompts_path) else []

    if args.dry_run:
        print("共 " + str(len(prompts)) + " 条 prompt：")
        for i, q in enumerate(prompts, 1):
            print("  [" + format(i, "02d") + "] " + q)
        return

    out_dir = os.path.join(HERE, "data")
    os.makedirs(out_dir, exist_ok=True)

    if args.batch:
        if not prompts:
            print("prompts.txt 为空"); return
        print("批量：" + str(len(prompts)) + " 条 → " + out_dir)
        print("确认 Alice Chat 已开。5 秒后开始。")
        countdown(5)
        for i, q in enumerate(prompts, 1):
            seq = next_seq(out_dir)
            print("\n[" + format(i, "02d") + "] " + q)
            run_one(q, seq, out_dir, args.min_wait, args.max_wait, args.stable_window, args.poll_interval)
            time.sleep(args.gap_between)
        print("\n完成。人工检查 " + out_dir)
        return

    if args.prompt:
        q = args.prompt
    elif args.index:
        if args.index < 1 or args.index > len(prompts):
            print("--index 超出范围（1.." + str(len(prompts)) + "）"); return
        q = prompts[args.index - 1]
    else:
        if not prompts:
            print("prompts.txt 为空，请用 --prompt"); return
        q = prompts[0]

    seq = next_seq(out_dir)
    print("single-run：seq=" + str(seq) + " → " + q)
    countdown(5)
    run_one(q, seq, out_dir, args.min_wait, args.max_wait, args.stable_window, args.poll_interval)


if __name__ == "__main__":
    main()
