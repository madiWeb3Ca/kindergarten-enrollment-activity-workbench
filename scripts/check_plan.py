#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验招生活动方案卡的结构与红线。

支持 .md 与 .html 两种文件（HTML 会先转成纯文本再走同一套规则）。

用法：
    python check_plan.py 方案卡.html
    python check_plan.py 方案卡.md --strict   # 警告也按错误处理

退出码：0 = 通过（可含警告）；1 = 有错误（缺段/红线硬伤）；2 = 文件读取失败。
"""

import argparse
import html as html_mod
import os
import re
import sys

REQUIRED_SECTIONS = [
    ("入口与目标", r"^\s*#+\s*.*(入口与目标|定入口|先定招谁)"),
    ("原型选择", r"^\s*#+\s*.*(原型选择|选原型|现成样子)"),
    ("流程环节", r"^\s*#+\s*.*(流程环节|活动过程|搭出本场方案)"),
    ("物料与分工", r"^\s*#+\s*.*(物料与分工|物料|分工)"),
    ("量力校验", r"^\s*#+\s*.*(量力校验|掂量够不够做)"),
    ("风险预案", r"^\s*#+\s*.*风险预案"),
    ("留资与落表", r"^\s*#+\s*.*(留资|落表|线索|当天怎么留)"),
    ("复盘与回流", r"^\s*#+\s*.*(复盘|回流|回头看|存下下次)"),
]

# 产物类型识别：单场方案卡 / 系列排期表 / 资源建档骨架
def detect_kind(text):
    if "排期表" in text:
        return "series"
    if "外联资源建档" in text:
        return "resource"
    return "single"

# 承诺性表述（红线，出现即错误）
PROMISE_PATTERNS = [
    r"保证招满", r"保证报名", r"转化率\s*\d+\s*%", r"招满\s*\d+",
    r"提升营收\s*\d+", r"曝光\s*\d+\s*%", r"报名人数\s*\d+\s*人",
    r"保证到场", r"百分百", r"100%\s*报名",
]

# 入口未清信号
ALL_FAMILY_PATTERNS = [r"面向\s*0\s*[-–~]\s*6\s*岁\s*所有家庭", r"面向所有家庭", r"全年龄段"]

# 延时课/兴趣班被当成引流产品
EXTENDED_COURSE = [r"延时课.*招生", r"兴趣班.*招生引流", r"选修课.*对外招生"]

# 现场不应追问的字段
EXTRA_FIELDS = ["出生日期", "性别", "参与人姓名"]

# 否定/排除语境：出现在这些语境里不算违规
NEGATIVE_HINTS = ["不进", "不属于", "在读", "增值服务", "另收费", "不打包",
                  "留到", "不追", "回访", "阶段补", "不收集", "不写进", "剔除"]


def in_negative_context(line, patterns):
    """行内是否同时含否定语境；边界说明（如'延时课不进招生清单'）不算违规。"""
    if any(h in line for h in NEGATIVE_HINTS):
        return True
    return False


def html_to_text(src):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", src)
    s = re.sub(r"(?is)<h1[^>]*>", "\n\n# ", s)
    s = re.sub(r"(?is)<h2[^>]*>", "\n\n## ", s)
    s = re.sub(r"(?is)<h3[^>]*>", "\n\n### ", s)
    s = re.sub(r"(?is)</h[123]>", "\n", s)
    s = re.sub(r"(?is)<tr[^>]*>", "\n| ", s)
    s = re.sub(r"(?is)</tr>", " |", s)
    s = re.sub(r"(?is)<t[dh][^>]*>", "", s)
    s = re.sub(r"(?is)</t[dh]>", " | ", s)
    s = re.sub(r"(?is)<li[^>]*>", "\n- ", s)
    s = re.sub(r"(?is)</li>", "", s)
    s = re.sub(r"(?is)<br[^>]*>", "\n", s)
    s = re.sub(r"(?is)<(p|div|section|header|footer|main|ul|table|thead|tbody)[^>]*>", "\n", s)
    s = re.sub(r"(?is)</(p|div|section|header|footer|main|ul|table|thead|tbody)>", "\n", s)
    s = re.sub(r"(?is)<[^>]+>", "", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s


def find_section(text, pattern):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(pattern, line):
            body = []
            for j in range(i + 1, len(lines)):
                if re.match(r"^\s*#{1,2}\s", lines[j]):
                    break
                body.append(lines[j])
            return i, "\n".join(body)
    return -1, ""


def main():
    parser = argparse.ArgumentParser(description="校验招生活动方案卡")
    parser.add_argument("path", help="方案卡文件（.md 或 .html）")
    parser.add_argument("--strict", action="store_true", help="警告也按错误处理")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"[错误] 文件不存在：{args.path}", file=sys.stderr)
        return 2
    if os.path.isdir(args.path):
        print(f"[错误] 传入的是文件夹，请指定具体的方案卡文件：{args.path}", file=sys.stderr)
        return 2

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        print("[错误] 文件编码无法识别，请另存为 UTF-8 编码后再校验", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"[错误] 文件读取失败：{e}", file=sys.stderr)
        return 2

    if not text.strip():
        print("[错误] 文件内容为空，请先填写方案卡再校验", file=sys.stderr)
        return 2

    if os.path.splitext(args.path)[1].lower() in (".html", ".htm"):
        text = html_to_text(text)

    errors, warnings = [], []
    kind = detect_kind(text)

    # 1. 章节齐全（仅单场方案卡；排期表/资源建档走各自模板）
    bodies = {}
    if kind == "single":
        for name, pattern in REQUIRED_SECTIONS:
            idx, body = find_section(text, pattern)
            if idx < 0:
                errors.append(f"缺少必需段落「{name}」")
            else:
                bodies[name] = body

        # 2. 入口卡是否定清
        entry = bodies.get("入口与目标", "")
        if entry:
            if not re.search(r"P\d|岁", entry):
                errors.append("入口段未锁定主攻年龄层")
            if not re.search(r"秋季|春季|蓄水", entry):
                warnings.append("入口段未写明招生窗口（秋季 9 月／春季 3 月／长期蓄水）")
            if not re.search(r"留资|品牌", entry):
                warnings.append("入口段未写明主目标（留资为主／品牌为主）")

        # 2b. 走出去场应有两场链路
        if "走出去" in text and not re.search(r"第二场|请进来|探园|体验课", text):
            warnings.append("走出去场建议写明两场链路（走出去留资 → 请进来体验/探园）")

        # 2c. 风险预案段应留降级档位
        risk = bodies.get("风险预案", "")
        if risk and "降级" not in risk:
            warnings.append("风险预案段未留降级预案档位（撑不住时按顺序砍环节/规模）")

    # 3. 承诺性红线
    for pat in PROMISE_PATTERNS:
        m = re.search(pat, text)
        if m:
            errors.append(f"出现承诺性表述：「{m.group(0)}」；指标只记过程事实，不承诺结果")

    # 4. 入口未清
    for pat in ALL_FAMILY_PATTERNS:
        m = re.search(pat, text)
        if m:
            errors.append(f"入口未锁定：「{m.group(0)}」；一场活动应聚焦主攻年龄层")

    # 5. 延时课被当引流产品（逐行排除否定/边界说明语境）
    for line in text.splitlines():
        for pat in EXTENDED_COURSE:
            m = re.search(pat, line)
            if m and not in_negative_context(line, EXTENDED_COURSE):
                errors.append(f"延时课/兴趣班是在读增值服务，不能打包成对外招生引流产品：「{m.group(0)}」")

    # 6. 现场多余字段（警告；排除"留到回访再补"这类说明语境）
    lead = bodies.get("留资与落表", "")
    for line in lead.splitlines():
        for f in EXTRA_FIELDS:
            if f in line and not in_negative_context(line, EXTRA_FIELDS):
                warnings.append(f"现场表单出现「{f}」，建议留到回访或 H5 阶段补，现场不追问")

    # 7. 未核实金额/名额（无占位标注）
    placeholder = "待核实" in text or "待填" in text
    money = re.search(r"(费用|收费|名额|人数)\s*[：:]\s*【?待", text)
    if not money and not placeholder:
        warnings.append("未见【待核实/待填】占位；费用、名额、联系人等未确认项须显式占位")

    # 汇总输出
    print(f"=== 校验结果：{args.path} ===")
    if errors:
        print(f"\n[错误] {len(errors)} 项（必须修）")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"\n[警告] {len(warnings)} 项（建议修）")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("\n[通过] 结构完整，红线项无告警")
    elif not errors:
        print("\n[通过] 结构完整（有警告，建议修改后再交付）")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
