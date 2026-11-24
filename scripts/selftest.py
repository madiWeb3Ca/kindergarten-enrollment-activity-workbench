#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冒烟测试：验证 scaffold、render_html 与 check 三个脚本的行为符合规范。

用法：python selftest.py
退出码：0 = 全部通过；1 = 有用例失败。
"""

import os
import re
import subprocess
import sys
import tempfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SCAFFOLD = os.path.join(HERE, "scaffold_plan.py")
CHECK = os.path.join(HERE, "check_plan.py")
RENDER = os.path.join(HERE, "render_html.py")
INIT = os.path.join(HERE, "init_tables.py")
DELIVER = os.path.join(HERE, "check_deliverables.py")
SKILL_MD = os.path.join(HERE, "..", "SKILL.md")


def skill_version():
    """从 SKILL.md frontmatter 读取版本号；读不到时返回占位，不阻断自测。"""
    try:
        with open(SKILL_MD, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^version:\s*([^\s#]+)", line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return "未知版本"

GOOD = """# 社区亲子坊（示例）

**场次编码**：2027Q1-某社区-01　**日期/时段**：【待核实：首场日期】
**场地**：某社区活动中心　**主攻年龄层**：P1 2.5–3 岁　**决策窗口**：长期蓄水　**主目标**：留资为主

## 一、先定招谁

- 主攻年龄层：P1 2.5–3 岁，兼容 P2 1.5–3 岁
- 决策窗口：面向 2027 秋季 9 月入园，蓄水池
- 主目标/副目标：留资为主，品牌曝光副目标
- 两场链路：第一场留资 → 第二场园内体验课/探园日

## 二、手里有什么（自家）

| 类别 | 本场可用 | 转化假设（能变成什么触点） | 待清点/待核实 |
|---|---|---|---|
| 师资 | 中教、外教可出场 | 中教带读＋外教 10 分钟手指谣 | 【待核实：档期】 |

## 三、找个现成样子

- 参考样子：社区亲子绘本坊
- 本场变形点：低龄安静环节，分段答疑

## 三补、推荐动作与本场亮点

- 首选动作：绘本共读打底，旁观位开放给犹豫家庭
- 超预期亮点：孩子作品自愿留影；对照应变库高频条目预读临场分支

## 四、手里有什么（周边）

| 项 | 口径 | 状态 |
|---|---|---|
| 场地 | 社区活动中心室内 | 【待核实：容量】 |

## 五、搭出本场方案

| 时段 | 环节 | 责任人 | 要点 |
|---|---|---|---|
| 0–10' | 签到登记 | 登记协助 | 发场次编号 |
| 10–25' | 绘本阅读 | 中教 | 低龄安静活动 |
| 25–35' | 外教穿插 | 外教 | 手指谣打招呼 |
| 35–50' | 分段答疑 | 招生答疑 | 不开讲座 |

## 六、物料与分工

- 园所出：老师、内容、物料、留资码、登记
- 合作方出：场地、通知、协助

## 七、掂量够不够做

| 维度 | 状态 | 缺口处置 |
|---|---|---|
| 人手 | 现成 | 中教、外教、答疑、登记协助各 1 |
| 留资工具 | 待核 | 纸质兜底先行 |

能不能做：补缺口后可执行

## 八、预算（占位待核）

- 人手＋常规物料＋小额伴手礼；【待核实：单价总额】

## 九、风险预案

- 儿童安全：场地排查尖角软包、留安静角落
- 超员：报名设上限
- 留资自愿：不强迫填写
- 口径合规：不贬同行、不编事实

## 十、当天怎么留线索

| 码 | 用途 | 何时扫 |
|---|---|---|
| 留资活码 | 极简表单＋领礼，带场次编号 | 现场 |
| 探园邀约码 | 选时段、填参与人 | 回家再扫 |

现场只收：孩子称呼、月龄段、家长称呼、电话或微信、意向勾选。

## 十一、回头看与存下下次用

- 复盘三问：断在哪一环；家长反馈什么；哪里要改。
- 存到资源库与原型配方。
"""

BAD = """# 社区招生活动

**主攻年龄层**：面向 0–6 岁所有家庭

## 一、入口与目标

- 保证招满 30 人，转化率 50%
- 主目标：品牌曝光

## 三、原型选择（③）

- 社区驻点

## 五、流程环节（④）

| 时段 | 环节 |
|---|---|
| 0–30' | 自由活动 |
"""


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def case(name, cond, detail=""):
    if cond:
        print(f"[通过] {name}")
        return True
    print(f"[失败] {name}　{detail}")
    return False


def main():
    print(f"=== 技能版本 {skill_version()}｜自测日期 {date.today().isoformat()} ===")
    results = []
    tmp = tempfile.mkdtemp(prefix="eaw_selftest_")

    # 用例 1：合格方案卡应通过校验
    good_path = os.path.join(tmp, "good.md")
    with open(good_path, "w", encoding="utf-8") as f:
        f.write(GOOD)
    r = run([sys.executable, CHECK, good_path])
    results.append(case("1 合格方案卡通过校验", r.returncode == 0 and "[通过]" in r.stdout,
                        r.stdout[-200:]))

    # 用例 2：缺陷方案卡（承诺＋入口未清＋缺段）应判不通过
    bad_path = os.path.join(tmp, "bad.md")
    with open(bad_path, "w", encoding="utf-8") as f:
        f.write(BAD)
    r = run([sys.executable, CHECK, bad_path])
    results.append(case("2 缺陷方案卡被拦截", r.returncode == 1 and "[错误]" in r.stdout,
                        r.stdout[-200:]))

    # 用例 3：正常生成单场骨架，章节齐全且能被校验脚本读取
    out = os.path.join(tmp, "社区亲子坊.html")
    r = run([sys.executable, SCAFFOLD, "--title", "社区亲子坊", "--layer", "P1",
             "--window", "长期蓄水", "--kind", "single", "--mode", "走出去",
             "--goal", "留资", "--out", out])
    ok = r.returncode == 0 and os.path.exists(out)
    if ok:
        with open(out, "r", encoding="utf-8") as f:
            content = f.read()
        sections = ["先定招谁", "现成样子", "搭出本场", "物料", "掂量",
                    "风险预案", "推荐动作", "当天怎么留", "回头看",
                    "供需交换象限", "投入档位", "赠品"]
        ok = all(s in content for s in sections)
        r = run([sys.executable, CHECK, out])
        ok = ok and r.returncode != 2
    results.append(case("3 单场骨架生成且章节齐全", ok, r.stderr[:200]))

    # 用例 4：缺必填参数（--title）应报错退出
    r = run([sys.executable, SCAFFOLD])
    results.append(case("4 缺必填参数报错", r.returncode != 0, r.stderr[:200]))

    # 用例 5：骨架 md 不含承诺性红线词，且可被校验读取
    md_out = os.path.join(tmp, "骨架.md")
    r = run([sys.executable, SCAFFOLD, "--title", "探园日", "--layer", "P0",
             "--window", "秋季", "--kind", "single", "--mode", "请进来",
             "--goal", "留资", "--format", "md", "--out", md_out])
    ok = r.returncode == 0 and os.path.exists(md_out)
    if ok:
        with open(md_out, "r", encoding="utf-8") as f:
            md_text = f.read()
        ok = not any(w in md_text for w in ["保证招满", "转化率", "提升营收"])
        r2 = run([sys.executable, CHECK, md_out])
        ok = ok and r2.returncode != 2
    results.append(case("5 骨架 md 无红线词且可读", ok, r.stderr[:200]))

    # 用例 6：缺陷件转成 HTML 后仍必须被拦截（HTML 路径不能空转）
    html_path = os.path.join(tmp, "bad.html")
    r = run([sys.executable, RENDER, bad_path, "-o", html_path])
    ok = r.returncode == 0 and os.path.exists(html_path)
    if ok:
        r = run([sys.executable, CHECK, html_path])
        ok = r.returncode == 1 and "[错误]" in r.stdout
    results.append(case("6 HTML 缺陷件同样被拦截", ok,
                        r.stdout[-200:] if r.stdout else r.stderr[:200]))

    # 用例 7：模式 B 排期表骨架生成，可被校验读取且不误报单场缺段
    series_out = os.path.join(tmp, "排期表.md")
    r = run([sys.executable, SCAFFOLD, "--title", "2027 春季排期", "--kind", "series",
             "--window", "春季", "--format", "md", "--out", series_out])
    ok = r.returncode == 0 and os.path.exists(series_out)
    if ok:
        with open(series_out, "r", encoding="utf-8") as f:
            content = f.read()
        ok = "排期一览" in content
        r2 = run([sys.executable, CHECK, series_out])
        ok = ok and r2.returncode == 0
    results.append(case("7 模式 B 排期表骨架通过校验", ok,
                        (r2.stdout[-200:] if ok else r.stderr[:200])))

    # 用例 8：模式 C 资源建档骨架生成，可被校验读取
    res_out = os.path.join(tmp, "资源建档.md")
    r = run([sys.executable, SCAFFOLD, "--title", "某社区活动中心", "--kind", "resource",
             "--format", "md", "--out", res_out])
    ok = r.returncode == 0 and os.path.exists(res_out)
    if ok:
        with open(res_out, "r", encoding="utf-8") as f:
            content = f.read()
        ok = "基础信息" in content and "接洽情况" in content
        r2 = run([sys.executable, CHECK, res_out])
        ok = ok and r2.returncode == 0
    results.append(case("8 模式 C 资源建档骨架通过校验", ok,
                        (r2.stdout[-200:] if ok else r.stderr[:200])))

    # 用例 9：底座表初始化（auto 先试 Excel，缺库落 MD；另验 MD 兜底）
    init_base = os.path.join(tmp, "底座表")
    r = run([sys.executable, INIT, "--out", init_base, "--format", "auto"])
    xlsx_path = init_base + ".xlsx"
    md_path = init_base + ".md"
    ok = r.returncode == 0
    if os.path.exists(xlsx_path):
        try:
            from openpyxl import load_workbook
            wb = load_workbook(xlsx_path)
            names = [ws.title for ws in wb.worksheets]
            archive = next(ws for ws in wb.worksheets if ws.title == "活动档案表")
            resource = next(ws for ws in wb.worksheets if ws.title == "外联资源库表")
            ok = ok and len(names) == 2 and archive.max_column == 26 and resource.max_column == 22
        except ImportError:
            ok = ok and os.path.exists(md_path)
    else:
        ok = ok and os.path.exists(md_path)
    r_md = run([sys.executable, INIT, "--out", os.path.join(tmp, "底座表md"), "--format", "md"])
    md2 = os.path.join(tmp, "底座表md.md")
    if os.path.exists(md2):
        with open(md2, "r", encoding="utf-8") as f:
            md_text = f.read()
        ok = ok and r_md.returncode == 0 and "活动档案表" in md_text and "外联资源库表" in md_text
    else:
        ok = False
    results.append(case("9 底座表初始化（Excel/MD 兜底）通过", ok,
                        (r.stderr[:200] or r_md.stderr[:200])))

    # 用例 10：执行手册骨架生成，六阶段与速查表齐全
    man_out = os.path.join(tmp, "社区亲子坊_执行手册.md")
    r = run([sys.executable, SCAFFOLD, "--title", "社区亲子坊", "--kind", "manual",
             "--mode", "走出去", "--layer", "P1", "--window", "长期蓄水", "--goal", "留资",
             "--format", "md", "--out", man_out])
    ok = r.returncode == 0 and os.path.exists(man_out)
    if ok:
        with open(man_out, "r", encoding="utf-8") as f:
            man_text = f.read()
        sections = ["对接定场", "定方案", "通知与工具", "备课物料", "当天执行",
                    "跟进与复盘", "速查表"]
        ok = all(s in man_text for s in sections)
    results.append(case("10 执行手册骨架生成且六阶段齐全", ok, r.stderr[:200]))

    # 用例 10b：手册过单文件校验，不误报方案卡专属段落缺失
    r10b = run([sys.executable, CHECK, man_out])
    ok10b = r10b.returncode == 0 and "缺少必需段落" not in r10b.stdout
    results.append(case("10b 手册校验不误报方案卡缺段", ok10b, r10b.stdout[-200:]))

    # 用例 11：目录级产物齐套检查（齐套 / 缺手册告警 / 豁免跳过 / 模式 B 不误报）
    def _touch(dirname, fname, content=""):
        d = os.path.join(tmp, dirname)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, fname)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return d

    # 11a 齐套：方案卡 HTML＋MD＋执行手册 HTML
    d_full = _touch("deliver_full", "方案卡.html")
    _touch("deliver_full", "方案卡.md")
    _touch("deliver_full", "执行手册.html")
    r = run([sys.executable, DELIVER, d_full])
    ok = r.returncode == 0 and "产物齐套" in r.stdout
    results.append(case("11a 齐套目录通过检查", ok, r.stdout[-200:]))

    # 11b 现场场缺手册：应出警告但不阻断
    d_noman = _touch("deliver_nomanual", "方案卡.html")
    _touch("deliver_nomanual", "方案卡.md")
    r = run([sys.executable, DELIVER, d_noman])
    ok = r.returncode == 0 and "缺执行手册" in r.stdout
    results.append(case("11b 缺执行手册给出警告", ok, r.stdout[-200:]))

    # 11c 标注手册豁免：跳过手册检查（方案卡 HTML/MD 仍在）
    d_exempt = _touch("deliver_exempt", "方案卡.html")
    _touch("deliver_exempt", "方案卡.md", "手册豁免：纯线上蓄水场，无线下现场环节")
    r = run([sys.executable, DELIVER, d_exempt])
    ok = r.returncode == 0 and "缺执行手册" not in r.stdout and "手册豁免" in r.stdout
    results.append(case("11c 手册豁免标注后跳过手册检查", ok, r.stdout[-200:]))

    # 11d 模式 B 排期表：不误报手册/底稿缺失
    d_series = _touch("deliver_series", "2027春季排期表.md")
    r = run([sys.executable, DELIVER, d_series])
    ok = r.returncode == 0 and "不要求执行手册" in r.stdout
    results.append(case("11d 排期表不误报现场场缺件", ok, r.stdout[-200:]))

    # 11e 异业/联动场缺供需象限：出软警告（不阻断；必备段齐全，returncode 0）
    cross_md = os.path.join(tmp, "异业缺供需.md")
    with open(cross_md, "w", encoding="utf-8") as f:
        f.write(GOOD + "\n- 本场为异业合作场，与周边机构联合筹备。\n")
    r = run([sys.executable, CHECK, cross_md])
    ok = r.returncode == 0 and "供需交换象限" in r.stdout
    results.append(case("11e 异业场缺供需象限给软警告", ok, r.stdout[-200:]))

    # 11f P4 超长周期场默认派人：出软警告（不阻断；必备段齐全，returncode 0）
    p4_text = GOOD.replace("P1 2.5–3 岁", "P4 0–1.5 岁").replace(
        "中教、外教、答疑、登记协助各 1", "派 3 人到场办活动")
    p4_md = os.path.join(tmp, "p4派人.md")
    with open(p4_md, "w", encoding="utf-8") as f:
        f.write(p4_text)
    r = run([sys.executable, CHECK, p4_md])
    ok = r.returncode == 0 and "轻型物料植入或线上蓄水" in r.stdout
    results.append(case("11f P4 场默认派人给软警告", ok, r.stdout[-200:]))

    # 用例 12：新增硬承诺词（包录取/保证进）必须被错误拦截
    promise_text = GOOD + "\n- 当场承诺包录取、保证进园名额。\n"
    promise_md = os.path.join(tmp, "硬承诺新词.md")
    with open(promise_md, "w", encoding="utf-8") as f:
        f.write(promise_text)
    r = run([sys.executable, CHECK, promise_md])
    ok = r.returncode == 1 and "包录取" in r.stdout
    results.append(case("12 新增硬承诺词被错误拦截", ok, r.stdout[-200:]))

    # 用例 13：绝对化/逼单/虚假口碑词出软警告但不阻断（returncode 0）
    soft_text = GOOD + "\n- 名额仅剩最后 5 席，家长好评如潮。\n"
    soft_md = os.path.join(tmp, "营销敏感词.md")
    with open(soft_md, "w", encoding="utf-8") as f:
        f.write(soft_text)
    r = run([sys.executable, CHECK, soft_md])
    ok = r.returncode == 0 and "营销敏感表述" in r.stdout
    results.append(case("13 营销敏感词给软警告不阻断", ok, r.stdout[-200:]))

    # 用例 14：资源建档骨架用新接洽状态枚举，不含旧值（未接洽/已接洽）
    res2 = os.path.join(tmp, "资源建档2.md")
    r = run([sys.executable, SCAFFOLD, "--title", "某妇幼机构", "--kind", "resource",
             "--format", "md", "--out", res2])
    ok = r.returncode == 0 and os.path.exists(res2)
    if ok:
        with open(res2, "r", encoding="utf-8") as f:
            res_text = f.read()
        ok = ("未对接" in res_text and "未接洽" not in res_text
              and "已接洽" not in res_text)
    results.append(case("14 资源骨架接洽状态枚举为新值", ok, r.stderr[:200]))

    # 用例 15：examples 目录下全部官方示例方案卡校验 0 错误（可含软警告）
    ex_dir = os.path.join(HERE, "..", "examples")
    ex_ok = True
    last_out = ""
    ex_files = [f for f in os.listdir(ex_dir) if f.endswith(".md")] if os.path.isdir(ex_dir) else []
    for fn in ex_files:
        r = run([sys.executable, CHECK, os.path.join(ex_dir, fn)])
        ex_ok = ex_ok and r.returncode == 0
        last_out = r.stdout[-200:]
    results.append(case("15 官方示例校验无错误", ex_ok and bool(ex_files), last_out))

    # 用例 16：再次进入回填触发规则在各篇挂钩一致（触发口径/未闭环/召回小卡/术语/FAQ）
    def _read(rel):
        p = os.path.join(HERE, "..", rel)
        try:
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    checks = {
        "SKILL.md": ["未闭环", "纯翻旧报告"],
        "references/review-loop.md": ["未闭环判定", "纯回看", "最小集"],
        "references/coaching-scripts.md": ["召回小卡", "待核实"],
        "references/proactive-playbook.md": ["未闭环"],
        "references/glossary.md": ["再次进入回填触发"],
        "references/faq.md": ["Q24"],
    }
    doc_ok = True
    doc_detail = ""
    for rel, keys in checks.items():
        text = _read(rel)
        missing = [k for k in keys if k not in text]
        if missing:
            doc_ok = False
            doc_detail = f"{rel} 缺 {missing}"
    results.append(case("16 回填触发规则各篇挂钩一致", doc_ok, doc_detail))

    print(f"\n=== {sum(results)}/{len(results)} 用例通过 ===")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
