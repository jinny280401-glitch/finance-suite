#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
隔离验证「抓取 + 锚点解析」段 —— 不发 query。

用途：Alice 界面上已有一条完整回答时，单独验证
  ① wind_focus capture 能否把全页文本抓出来（UTF-8 修复后）
  ② extract_last_answer 的锚点（分享 / 内容由AI生成）能否从全页 raw 里切出回答

跑法（界面停在那条北方华创回答上）：
  python3 verify_capture.py

落 data/capture_verify.json，并在终端打印 raw 长度 / parse_status / 切出的回答前后各一段。
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FOCUS_BIN = os.path.join(HERE, "wind_focus")

# 复用 runner 的锚点解析（同一份逻辑，避免两套）
sys.path.insert(0, HERE)
from run_alice_poc import extract_last_answer, ANCHOR_START, ANCHOR_END  # noqa: E402


def capture():
    r = subprocess.run([FOCUS_BIN, "capture"], capture_output=True)
    raw = r.stdout.decode("utf-8", errors="replace")
    err = r.stderr.decode("utf-8", errors="replace").strip()
    return raw, err, r.returncode


def main():
    if not os.path.exists(FOCUS_BIN):
        print("wind_focus 未编译"); return
    raw, err, rc = capture()
    print("=== wind_focus capture ===")
    print("rc:", rc, "| stderr:", err)
    print("raw 长度:", len(raw))

    # 锚点命中情况
    s = raw.find(ANCHOR_START)
    e = raw.find(ANCHOR_END)
    print(f"锚点 '{ANCHOR_START}' 位置: {s}   '{ANCHOR_END}' 位置: {e}")

    answer, parse_status = extract_last_answer(raw, "北方华创 最近三个月的核心分歧点是什么？")
    print("parse_status:", parse_status)
    print("answer 长度:", len(answer))
    print("--- answer 前 150 字 ---")
    print(answer[:150])
    print("--- answer 后 80 字 ---")
    print(answer[-80:])

    out_dir = os.path.join(HERE, "data")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "capture_verify.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "raw_len": len(raw),
            "anchor_start_pos": s,
            "anchor_end_pos": e,
            "parse_status": parse_status,
            "answer_len": len(answer),
            "answer": answer,
            "raw_clipboard": raw,
        }, f, ensure_ascii=False, indent=2)
    print("\n落盘:", path)

    # 给出判定
    print("\n=== 判定 ===")
    if rc != 0:
        print("✗ 抓取失败（rc!=0）—— 焦点/Cmd+A 问题，不是解析问题")
    elif s == -1:
        print("✗ 全页 raw 里找不到 '分享' 锚点 —— 锚点失效或这条回答没有分享按钮文本，需换锚点")
    elif parse_status == "success":
        print("✓ 抓取 + 锚点解析都成功，answer 是切出来的回答（非全文）")
    elif parse_status == "partial":
        print("△ 抓到了但锚点切不准（answer 退化为全文）—— 需调锚点切段逻辑")
    else:
        print("✗ parse_status =", parse_status)


if __name__ == "__main__":
    main()
