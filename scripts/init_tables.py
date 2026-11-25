#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""初始化两张底座表：活动档案表、外联资源库表。

建表形态按环境能力三级降级（由对话里的 AI 先判断环境，再选产物）：
    1. 在线多维表格（首选）：环境具备豆包内置多维表格能力时，由 AI 直接按
       `tables/` 骨架新建，字段、单选选项、表间关联一次配完；本脚本不在线写表。
    2. 本地 Excel（兜底一）：环境不支持在线表时，生成本地 .xlsx 工作簿，
       两张 sheet 对应两张表，表头与单选选项按骨架落好。
    3. MD 文本（兜底二）：连 Excel 都生成不了时，输出 Markdown 表结构文本，
       供后续导入或誊录。

用法：
    python init_tables.py --out ./tables_out
    python init_tables.py --format xlsx --out ./tables_out
    python init_tables.py --format md
    python init_tables.py --tables archive

说明：字段口径以 `tables/activity-archive.md`、`tables/outreach-resource.md`
为准；本脚本只生成空表结构与一行占位，具体事实由使用者口述、AI 出初稿后回填。
"""

import argparse
import os
import sys

# 字段定义：name 表头；kind 类型；options 单选/多选选项（可空）；note 填写说明
ARCHIVE = {
    "sheet": "活动档案表",
    "fields": [
        {"name": "场次编码", "kind": "文本", "options": [], "note": "全场唯一，示例 2027Q1-某社区-01"},
        {"name": "日期", "kind": "日期", "options": [], "note": "活动实际日期；待排期留占位"},
        {"name": "活动名称", "kind": "文本", "options": [], "note": "家长和老师一眼能看懂今天干什么"},
        {"name": "场地/社区", "kind": "文本", "options": [], "note": "具体场所与所属社区/小区"},
        {"name": "场所编码", "kind": "关联", "options": [], "note": "关联外联资源库表对应场所条目"},
        {"name": "活动类型", "kind": "单选", "options": ["社区联动", "探园日", "开放日", "体验课", "线上引流", "异业联办", "其他"], "note": ""},
        {"name": "年龄段", "kind": "单选", "options": ["3–4岁", "2.5–3岁", "1.5–3岁", "4–5岁", "0–1.5岁"], "note": "对外用岁；与年龄层编号一一对应"},
        {"name": "年龄层编号", "kind": "单选", "options": ["P0", "P1", "P2", "P3", "P4"], "note": "内部分层编号；P0=3–4岁／P1=2.5–3岁／P2=1.5–3岁／P3=4–5岁／P4=0–1.5岁"},
        {"name": "决策窗口", "kind": "单选", "options": ["秋季9月入园", "春季3月入园", "长期蓄水"], "note": ""},
        {"name": "主目标", "kind": "单选", "options": ["留资为主", "品牌为主"], "note": "副目标另记"},
        {"name": "到场组数", "kind": "数值", "options": [], "note": "过程事实，不预设达标线"},
        {"name": "留资数", "kind": "数值", "options": [], "note": "现场留资家庭数"},
        {"name": "加微数", "kind": "数值", "options": [], "note": ""},
        {"name": "当场敲定", "kind": "数值", "options": [], "note": "现场敲定探园意向组数"},
        {"name": "H5预约", "kind": "数值", "options": [], "note": "离场后提交邀约 H5 组数"},
        {"name": "到园试听/探园", "kind": "数值", "options": [], "note": "链路第二场实际到园组数"},
        {"name": "后续报名", "kind": "数值", "options": [], "note": "复盘时回填；未成交不填推断值"},
        {"name": "出场人数", "kind": "数值", "options": [], "note": "本场出场老师/工作人员数"},
        {"name": "物料/伴手礼", "kind": "文本", "options": [], "note": "品项清单；单价总额占位待核"},
        {"name": "预算金额", "kind": "数值/占位", "options": [], "note": "待核，不编数字"},
        {"name": "断环环节", "kind": "文本", "options": [], "note": "对照漏斗写明流失最多的一环"},
        {"name": "家长反馈主题标签", "kind": "多选/文本", "options": [], "note": "关注点、顾虑、意见归类"},
        {"name": "改进项", "kind": "文本", "options": [], "note": "下次改哪一句、换哪个环节/物料"},
        {"name": "复盘日期", "kind": "日期", "options": [], "note": "正式复盘一般在链路第二场后"},
        {"name": "方案卡链接", "kind": "链接/附件", "options": [], "note": "HTML 方案卡挂本行或单独导出"},
        {"name": "本场创新动作/借鉴来源", "kind": "文本", "options": [], "note": "外来打法或自创亮点；标注借鉴行业/来源；无则留空"},
        {"name": "创新动作反馈标签", "kind": "多选/文本", "options": ["跑成", "一般", "未跑成"], "note": "附过程事实反馈；下场是否复用；不填主观推断"},
    ],
}

RESOURCE = {
    "sheet": "外联资源库表",
    "fields": [
        {"name": "场所编码", "kind": "文本", "options": [], "note": "全场唯一，关联活动档案表"},
        {"name": "名称", "kind": "文本", "options": [], "note": "社区/物业/商场/机构等全称"},
        {"name": "类型", "kind": "单选", "options": ["居委会", "物业", "商场", "亲子机构", "公园", "医院", "妇幼母婴机构", "儿童医疗健康机构", "其他"], "note": ""},
        {"name": "地址", "kind": "文本", "options": [], "note": "公开可查地址；待核留占位"},
        {"name": "距离车程", "kind": "文本", "options": [], "note": "直线距离/实测车程；车程待实测标注"},
        {"name": "来源", "kind": "单选", "options": ["POI种子", "在读家庭推荐", "老带新", "曾走访"], "note": ""},
        {"name": "对接人", "kind": "文本", "options": [], "note": "合作方联系人；未知留空不编"},
        {"name": "职务", "kind": "文本", "options": [], "note": ""},
        {"name": "联系方式", "kind": "文本", "options": [], "note": "电话/微信，受控保存"},
        {"name": "接洽状态", "kind": "单选", "options": ["未对接", "初步接触", "已对接", "已合作", "暂缓"], "note": ""},
        {"name": "合作方式", "kind": "多选", "options": ["驻点走出去", "联办请进来", "物料互放", "包场"], "note": ""},
        {"name": "费用", "kind": "文本/占位", "options": [], "note": "场地费等；待确认不编"},
        {"name": "容量", "kind": "文本", "options": [], "note": "可容纳家庭组数/人数"},
        {"name": "可办时段", "kind": "文本", "options": [], "note": "周末/工作日、上午/下午"},
        {"name": "室内外", "kind": "单选", "options": ["室内", "户外", "均可"], "note": ""},
        {"name": "雨天备选", "kind": "文本", "options": [], "note": "户外场所必填雨天方案"},
        {"name": "关联场次编码", "kind": "关联", "options": [], "note": "关联活动档案表"},
        {"name": "到场组数", "kind": "数值", "options": [], "note": "最近一场"},
        {"name": "留资数", "kind": "数值", "options": [], "note": "最近一场"},
        {"name": "转预约数", "kind": "数值", "options": [], "note": "最近一场"},
        {"name": "复盘备注", "kind": "文本", "options": [], "note": "合作顺畅度、通知渠道效果、下次注意点"},
        {"name": "更新日期", "kind": "日期", "options": [], "note": "最近一次接洽/复盘回填"},
    ],
}

TABLES = {"archive": ARCHIVE, "resource": RESOURCE}


def _xlsx_comment(field):
    """生成表头批注文本：类型＋选项＋说明。"""
    parts = [f"类型：{field['kind']}"]
    if field["options"]:
        parts.append("选项：" + "／".join(field["options"]))
    if field["note"]:
        parts.append(field["note"])
    return "；".join(parts)


def write_xlsx(tables, out_path):
    try:
        from openpyxl import Workbook
        from openpyxl.comments import Comment
        from openpyxl.styles import Font, Alignment
    except ImportError:
        return False, "缺少 openpyxl，无法生成 Excel"

    wb = Workbook()
    wb.remove(wb.active)
    header_font = Font(bold=True)
    for t in tables:
        ws = wb.create_sheet(title=t["sheet"][:31])
        headers = [f["name"] for f in t["fields"]]
        ws.append(headers)
        for col_idx, field in enumerate(t["fields"], start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            comment_text = _xlsx_comment(field)
            if comment_text:
                cell.comment = Comment(comment_text, "skill")
            ws.column_dimensions[cell.column_letter].width = max(12, min(22, len(field["name"]) * 2 + 4))
        # 一行占位，便于使用者识别填写位置
        ws.append(["【待填】"] * len(headers))
        ws.freeze_panes = "A2"
    try:
        wb.save(out_path)
    except OSError:
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except OSError:
                pass
        raise
    return True, out_path


def _md_table(t):
    headers = [f["name"] for f in t["fields"]]
    lines = [f"## {t['sheet']}", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "---|" * len(headers))
    lines.append("| " + " | ".join(["【待填】"] * len(headers)) + " |")
    lines.append("")
    lines.append("> 字段类型与选项：")
    for f in t["fields"]:
        opt = ("；选项：" + "／".join(f["options"])) if f["options"] else ""
        note = ("；" + f["note"]) if f["note"] else ""
        lines.append(f"- {f['name']}（{f['kind']}{opt}）{note}")
    return "\n".join(lines)


def write_md(tables, out_path):
    body = ["# 底座表 · 初始化结构（MD 兜底）", "",
            "> 在线多维表格不可用、Excel 也生成不了时使用；按以下表头建表，单选/多选选项见各字段说明。", ""]
    for t in tables:
        body.append(_md_table(t))
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(body))
    except OSError:
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except OSError:
                pass
        raise
    return True, out_path


def main():
    parser = argparse.ArgumentParser(description="初始化活动档案表与外联资源库表（在线表之外的本地兜底产物）")
    parser.add_argument("--out", default=None, help="输出路径（目录或文件前缀，默认当前目录）")
    parser.add_argument("--format", choices=["auto", "xlsx", "md"], default="auto",
                        help="产物形态：auto 先试 xlsx 缺库落 md；xlsx 本地 Excel；md 文本")
    parser.add_argument("--tables", choices=["archive", "resource", "both"], default="both",
                        help="生成哪张表：archive 活动档案／resource 外联资源库／both 两张（默认）")
    args = parser.parse_args()

    if args.tables == "both":
        tables = [ARCHIVE, RESOURCE]
    else:
        tables = [TABLES[args.tables]]

    base = args.out or "init_tables"
    root, ext = os.path.splitext(base)
    out_dir = os.path.dirname(os.path.abspath(base))
    os.makedirs(out_dir, exist_ok=True)

    want_xlsx = args.format in ("auto", "xlsx")
    if want_xlsx:
        xlsx_path = root + ".xlsx"
        ok, msg = write_xlsx(tables, xlsx_path)
        if ok:
            print(f"[完成] 已生成本地 Excel：{xlsx_path}")
            print("[提示] 在线环境优先用豆包内置多维表格；本 Excel 为本地兜底产物")
            return 0
        if args.format == "xlsx":
            print(f"[错误] Excel 生成失败：{msg}", file=sys.stderr)
            return 2
        print(f"[降级] {msg}，改出 MD 文本")

    md_path = root + ".md"
    try:
        write_md(tables, md_path)
    except OSError as e:
        print(f"[错误] MD 文件写入失败：{e}", file=sys.stderr)
        return 2
    print(f"[完成] 已生成 MD 表结构：{md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
