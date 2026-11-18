#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冒烟测试：验证 scaffold、render_html 与 check 三个脚本的行为符合规范。

用法：python selftest.py
退出码：0 = 全部通过；1 = 有用例失败。
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCAFFOLD = os.path.join(HERE, "scaffold_plan.py")
CHECK = os.path.join(HERE, "check_plan.py")
RENDER = os.path.join(HERE, "render_html.py")

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
                    "风险预案", "当天怎么留", "回头看"]
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

    print(f"\n=== {sum(results)}/{len(results)} 用例通过 ===")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
