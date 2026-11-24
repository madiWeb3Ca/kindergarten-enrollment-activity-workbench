#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""目录级产物齐套检查：模式 A 单场活动的方案卡 / MD 底稿 / 执行手册是否缺件。

用法：
    python check_deliverables.py ./本场目录
    python check_deliverables.py ./本场目录/方案卡.html   # 传文件则查其所在目录

退出码：0 = 通过（可含警告）；1 = 有错误（主件缺失）；2 = 路径读取失败。

齐套规则：
- 模式 B 排期表、模式 C 资源建档：单件产物，不要求手册/底稿。
- 模式 A 现场场：方案卡 HTML 必出；方案卡 MD 底稿、执行手册 HTML 建议出。
- 方案卡文本标注「手册豁免」时，跳过手册检查（线上蓄水 / 纯物料植入等）。
"""

import argparse
import html as html_mod
import os
import re
import sys

CARD_KEY = "方案卡"
MANUAL_KEY = "执行手册"
SERIES_KEY = "排期表"
RESOURCE_KEY = "资源建档"
EXEMPT_MARK = "手册豁免"


def html_to_text(src):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", src)
    s = re.sub(r"(?is)<[^>]+>", " ", s)
    s = html_mod.unescape(s)
    return re.sub(r"\s+", " ", s)


def scan_dir(path):
    cards_html, cards_md, manuals = [], [], []
    series = resource = False
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if not os.path.isfile(full):
            continue
        low = name.lower()
        if SERIES_KEY in name:
            series = True
        if RESOURCE_KEY in name:
            resource = True
        if low.endswith(".html"):
            if CARD_KEY in name:
                cards_html.append(full)
            elif MANUAL_KEY in name:
                manuals.append(full)
        elif low.endswith(".md"):
            if CARD_KEY in name:
                cards_md.append(full)
    return cards_html, cards_md, manuals, series, resource


def read_text(full):
    try:
        with open(full, "r", encoding="utf-8") as f:
            raw = f.read()
    except (UnicodeDecodeError, OSError):
        return ""
    if full.lower().endswith(".html"):
        return html_to_text(raw)
    return raw


def main():
    parser = argparse.ArgumentParser(description="检查单场活动目录的产物齐套情况")
    parser.add_argument("path", help="本场目录，或目录内任一产物文件")
    args = parser.parse_args()

    target = args.path
    if not os.path.exists(target):
        print(f"[错误] 路径不存在：{target}", file=sys.stderr)
        return 2
    if os.path.isfile(target):
        target = os.path.dirname(os.path.abspath(target))
    if not os.path.isdir(target):
        print(f"[错误] 不是有效目录：{target}", file=sys.stderr)
        return 2

    try:
        cards_html, cards_md, manuals, series, resource = scan_dir(target)
    except OSError as e:
        print(f"[错误] 目录读取失败：{e}", file=sys.stderr)
        return 2

    errors, warnings, notes = [], [], []

    # 模式 B / C：单件产物，不套现场场齐套规则
    if series or resource:
        kind = "排期表" if series else "资源建档"
        notes.append(f"识别为模式 {'B' if series else 'C'}（{kind}），单件产物，不要求执行手册与 MD 底稿")
        if not (cards_html or cards_md or manuals):
            notes.append(f"未在目录中识别到{kind}文件，请核对文件名")
        print(f"=== 产物齐套检查：{target} ===")
        for n in notes:
            print(f"  · {n}")
        print("\n[通过] 非单场现场场，无强制齐套要求")
        return 0

    if not cards_html and not cards_md:
        print(f"=== 产物齐套检查：{target} ===")
        errors.append("未识别到模式 A 方案卡（文件名含「方案卡」的 .html/.md）；若为本场目录请先出方案卡")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    # 读方案卡文本，判断手册豁免
    card_text = ""
    for f in cards_html + cards_md:
        card_text += read_text(f)
    exempt = EXEMPT_MARK in card_text

    print(f"=== 产物齐套检查：{target} ===")
    if cards_html:
        notes.append(f"方案卡 HTML：{os.path.basename(cards_html[0])}")
    else:
        errors.append("缺方案卡 HTML 主件（单文件可离线阅读、打印存 PDF）")

    if cards_md:
        notes.append(f"方案卡 MD 底稿：{os.path.basename(cards_md[0])}")
    else:
        warnings.append("缺方案卡 .md 底稿（版本库比对/回流底版，建议补）")

    if manuals:
        notes.append(f"执行手册 HTML：{os.path.basename(manuals[0])}")
    elif exempt:
        notes.append("方案卡已标注「手册豁免」，按线上蓄水/纯物料植入等情形跳过手册检查")
    else:
        warnings.append("缺执行手册 HTML；有线下现场环节的单场活动应出步骤 SOP 手册（六阶段＋当天 checklist＋速查表）；如属线上蓄水/纯物料植入，请在方案卡标注「手册豁免＋原因」")

    for n in notes:
        print(f"  · {n}")
    if errors:
        print(f"\n[错误] {len(errors)} 项（必须修）")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"\n[警告] {len(warnings)} 项（建议补）")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("\n[通过] 产物齐套")
    elif not errors:
        print("\n[通过] 主件齐全（有警告，建议补齐后再交付）")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
