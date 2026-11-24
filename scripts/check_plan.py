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

# 方案卡标准章节顺序（与 plan-framework.md 第〇节一致），用于顺序校验。
# 仅在标题行（# 开头）匹配，避免正文里的同名词误判。
STANDARD_SECTION_ORDER = [
    ("入口与目标", r"(先定招谁|入口与目标|定入口)"),
    ("自家家底", r"手里有什么（自家|自家家底"),
    ("周边场地", r"手里有什么（周边"),
    ("供需交换象限", r"供需交换象限|供需"),
    ("原型选择", r"找个现成样子|原型选择|选原型"),
    ("流程环节", r"搭出本场方案|流程环节"),
    ("物料与分工", r"物料与分工"),
    ("量力校验", r"掂量够不够做|量力校验"),
    ("预算", r"预算"),
    ("风险预案", r"风险预案"),
    ("推荐动作与亮点", r"推荐动作"),
    ("留资与落表", r"当天怎么留线索|留资"),
    ("复盘与回流", r"回头看|复盘|回流"),
    ("待核实清单", r"待核实清单"),
]

# 产物类型识别：单场方案卡 / 执行手册 / 系列排期表 / 资源建档骨架
def detect_kind(text, path=""):
    base = os.path.basename(path) if path else ""
    if "执行手册" in base or "执行手册" in text[:200]:
        return "manual"
    if "排期表" in text:
        return "series"
    if "外联资源建档" in text:
        return "resource"
    return "single"

# 承诺结果/录取保证（红线，出现即错误）
PROMISE_PATTERNS = [
    r"保证招满", r"保证报名", r"保证到场", r"保证录取", r"保证进",
    r"包录取", r"包直升", r"包过",
    r"转化率\s*\d+\s*%", r"招满\s*\d+", r"提升营收\s*\d+", r"曝光\s*\d+\s*%",
    r"报名人数\s*\d+\s*人", r"百分百", r"100%\s*报名", r"100%\s*录取",
    r"稳招", r"抢报一空",
]

# 绝对化最高级/稀缺逼单/虚假口碑/利益诱导（软警告；否定与边界说明语境排除）
SOFT_MARKETING_PATTERNS = [
    r"排名第一", r"全网第一", r"口碑第一", r"最好的", r"最优", r"最强", r"顶级",
    r"最受欢迎", r"好评如潮", r"零差评", r"100%\s*好评", r"名额仅剩", r"名额不多",
    r"最后\s*\d+\s*席", r"名额紧张", r"限时抢购", r"限时优惠", r"分销返利",
    r"转介绍提成", r"拉人头返利",
]

# 入口未清信号
ALL_FAMILY_PATTERNS = [r"面向\s*0\s*[-–~]\s*6\s*岁\s*所有家庭", r"面向所有家庭", r"全年龄段"]

# 延时课/兴趣班被当成引流产品
EXTENDED_COURSE = [r"延时课.*招生", r"兴趣班.*招生引流", r"选修课.*对外招生"]

# 现场不应追问的字段
EXTRA_FIELDS = ["出生日期", "性别", "参与人姓名"]

# 否定/排除语境：出现在这些语境里不算违规
NEGATIVE_HINTS = ["不进", "不属于", "在读", "增值服务", "另收费", "不打包",
                  "留到", "不追", "回访", "阶段补", "不收集", "不写进", "剔除",
                  "不搞", "不设", "不买", "不排", "不做", "别", "勿", "禁止",
                  "替代", "对照", "不接", "不安排", "不承诺", "不攀比"]


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


def check_section_order(text):
    """按标准骨架核对标题行出现顺序，乱序返回错误信息。

    按标准顺序逐个定位章节第一个标题行，再比较实际行号是否单调递增；
    缺失章节由「章节齐全」逻辑另报，这里只对实际找到的章节判顺序。
    """
    lines = text.splitlines()
    located = []  # (标准序号, 名称, 行号)
    for order_idx, (name, pat) in enumerate(STANDARD_SECTION_ORDER):
        for i, line in enumerate(lines):
            if re.match(r"^\s*#+\s", line) and re.search(pat, line):
                located.append((order_idx, name, i))
                break

    order_errors = []
    prev_line, prev_name = -1, ""
    for order_idx, name, ln in located:
        if ln < prev_line:
            order_errors.append(
                f"章节顺序颠倒：「{prev_name}」应在「{name}」之前；"
                "标准顺序见 plan-framework.md 第〇节，不得调换章节顺序"
            )
        prev_line, prev_name = ln, name
    return order_errors


def _section_lines(text):
    """返回 (行列表, {章节键: 标题行号})，按标准骨架正则在标题行匹配。"""
    lines = text.splitlines()
    located = {}
    for name, pat in STANDARD_SECTION_ORDER:
        for i, line in enumerate(lines):
            if re.match(r"^\s*#+\s", line) and re.search(pat, line):
                located[name] = i
                break
    return lines, located


def check_prototype_forward_ref(lines, located):
    """前置引用：原型章（5）不得出现第六章才定义的“第 N 站”站点编号。"""
    proto = located.get("原型选择")
    flow = located.get("流程环节")
    if proto is None or flow is None:
        return []
    for i in range(proto + 1, flow):
        if re.search(r"第\s*\d+\s*站", lines[i]):
            return ["原型章（5）出现第六章才定义的站点编号“第 N 站”；经验依据按通用接触环节列，站点定义归第六章"]
    return []


def check_conclusion_before_risk(lines, located):
    """结论后置：可行性结论不得出现在风险预案章（10）之前。"""
    risk = located.get("风险预案")
    if risk is None:
        return []
    concl = re.compile(r"能不能做|补缺口后可执行|结论[:：]\s*可执行|可行性结论[:：]\s*[^见在指]")
    for i in range(0, risk):
        if concl.search(lines[i]):
            return ["可行性结论应放在预算、风险与降级之后；第八章只列缺口，不在风险预案前下“能不能做”结论"]
    return []


# 内容传播指标：只属于“官方号视频怎么传播”的调研，不能当活动设计同业依据
CONTENT_METRIC_PATTERN = (
    r"三平台|官方号|点赞|收藏|播放|涨粉|粉丝|爆款|视频号|抖音|小红书"
)


def check_content_metric_in_prototype(lines, located):
    """同业依据边界：原型章（5）同业列不得出现内容传播指标。"""
    proto = located.get("原型选择")
    flow = located.get("流程环节")
    if proto is None or flow is None:
        return []
    for i in range(proto + 1, flow):
        line = lines[i]
        m = re.search(CONTENT_METRIC_PATTERN, line)
        if m and not in_negative_context(line, []):
            return [
                "原型章（5）同业依据出现内容传播指标“三平台/官方号/点赞/收藏/播放/涨粉”等；"
                "同业依据只能引用真实活动案例，内容传播调研归视频/内容那条线，不得作为活动设计依据"
            ]
    return []


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
    kind = detect_kind(text, args.path)

    # 1. 章节齐全（仅单场方案卡；排期表/资源建档走各自模板）
    bodies = {}
    if kind == "single":
        for name, pattern in REQUIRED_SECTIONS:
            idx, body = find_section(text, pattern)
            if idx < 0:
                errors.append(f"缺少必需段落「{name}」")
            else:
                bodies[name] = body

        # 1b. 章节顺序校验（固定骨架，乱序即错误）
        errors.extend(check_section_order(text))

        # 1c. 前置引用与结论后置（软警告，防补丁）
        _lines, _located = _section_lines(text)
        warnings.extend(check_prototype_forward_ref(_lines, _located))
        warnings.extend(check_conclusion_before_risk(_lines, _located))
        # 1d. 同业依据边界：内容传播指标不得混入同业依据（软警告）
        warnings.extend(check_content_metric_in_prototype(_lines, _located))

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

        # 2d. 年龄层与活动形式错配（软警告；边界/否定语境不误报）
        layer_m = re.search(r"P([0-4])", entry)
        if layer_m:
            layer = layer_m.group(1)
            if layer == "2":
                for line in text.splitlines():
                    if re.search(r"探园日|开放日", line) and not in_negative_context(line, []):
                        warnings.append("P2 托班/亲子层通常承接低龄亲子体验；探园日/开放日更偏 P0 择园，核对活动形式是否与年龄层错配")
                        break
            if layer == "0":
                for line in text.splitlines():
                    if re.search(r"托班体验|亲子班体验", line) and not in_negative_context(line, []):
                        warnings.append("P0 择园层通常承接探园日/开放日/体验课；托班/亲子体验更偏 P2，核对是否错配")
                        break

        # 2e. 留资段挂场次编码（软警告，便于归因到具体场次）
        lead_body = bodies.get("留资与落表", "")
        if lead_body and re.search(r"活码|表单|留资|邀约码", lead_body):
            if not re.search(r"场次编码|场次编号|\d{4}Q\d", text):
                warnings.append("留资线索建议挂场次编码（YYYYQX-场所简称-序号），便于归因到具体场次")

        # 2f. 缺主动抓手/亮点动作（软警告：方案只有环节罗列，缺推荐动作或创意亮点）
        if not re.search(r"首选动作|稳妥备选|亮点|创意|超预期", text):
            warnings.append("方案卡建议补一段推荐动作/本场亮点（首选动作、稳妥备选、超预期亮点），避免只有环节罗列")

        # 2g. 缺临场应变兜底指针（软警告：未挂突发场景分支）
        if not re.search(r"应变|兜底分支|contingency|突发状况|突发场景", text):
            warnings.append("方案卡建议挂临场应变兜底指针，对照应变库高频条目预读本场最可能遇到的分支")

        # 2h. 异业/联动场缺供需交换象限（软警告：先盘双方供需再定分工）
        if re.search(r"异业|联动|外部机构", text) and not re.search(r"供需|我方需求|对方供给", text):
            warnings.append("异业/联动场建议先补供需交换象限（我方需求/对方需求/我方供给/对方供给→匹配判断→档位），再写分工与创意")

        # 2i. P4 超长周期场默认派人（软警告：应走轻型物料/线上蓄水档）
        if re.search(r"P4", text) and re.search(r"派人|到场|3\s*人|半天", text) and not re.search(r"轻型|物料植入|赞助|线上蓄水", text):
            warnings.append("P4 超长周期渠道建议走轻型物料植入或线上蓄水档，不默认派人到场")

    # 2h. 执行手册最小骨架（软检查：六阶段＋速查表是否在位）
    if kind == "manual":
        for needle in ["对接定场", "定方案", "通知与工具", "备课物料", "当天执行", "跟进与复盘", "速查表"]:
            if needle not in text:
                warnings.append(f"执行手册建议补「{needle}」阶段或附表")

    # 3. 承诺性红线
    for pat in PROMISE_PATTERNS:
        m = re.search(pat, text)
        if m:
            errors.append(f"出现承诺性表述：「{m.group(0)}」；指标只记过程事实，不承诺结果")

    # 3b. 绝对化/逼单/虚假背书/利益诱导（软警告；逐行排除否定与边界说明语境）
    for line in text.splitlines():
        for pat in SOFT_MARKETING_PATTERNS:
            m = re.search(pat, line)
            if m and not in_negative_context(line, SOFT_MARKETING_PATTERNS):
                warnings.append(f"出现营销敏感表述：「{m.group(0)}」；避免绝对化最高级、稀缺逼单、虚假口碑与利益诱导，只讲可查证事实")

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
