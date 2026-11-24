# 幼儿园招生活动工作台（kindergarten-enrollment-activity-workbench）

> 按八步思考路径带园所策划招生与社区外联活动，主动推荐动作与创意、跨行业借鉴策略、临场突发应变分支，产出可落地的活动方案卡、留资留痕与复盘回流记录。内核是**可教的思考过程＋自循环迭代**，不是案例库，也不是填好的现成模板。

## 一、适用与不适用

**适用**：单场招生/亲子/探园/体验课/社区联动/异业合作活动策划；招生季系列排期；外联资源库建档与复盘回流。

**不适用**：在园教学教案（用教案工作台）、短视频拍摄剪辑脚本、品牌卖点与策略底稿、家长个体跟进话术（用招生工作台）。

**能力边界**：不代运营账号、不接手日常内容排期；不承诺招生人数/转化率/报名结果；AI 初稿须人工复核事实、时间、联系人、费用、名额后对外。

## 二、目录结构

```
kindergarten-enrollment-activity-workbench/
├── SKILL.md                    # 技能主文件：定位、三模式、八步路径、硬规则、资源索引
├── README.md                   # 本文件（安装与上手说明）
├── CHANGELOG.md                # 版本变更记录
├── LICENSE                     # 许可协议（CC-BY-NC-SA-4.0）；源仓为 LICENSE，SkillHub 发布副本改名 LICENSE.md
├── references/                 # 备课与规则参考（AI 按需读取）
│   ├── entry-layers.md         # 第①步：年龄分层、政策口径、窗口节奏、产品边界
│   ├── coaching-scripts.md     # 八步教练式引导话术与追问链
│   ├── inventory-drawers.md    # 第②步：家底六抽屉、转化三问、数据参照口径
│   ├── activity-prototypes.md  # 第③步：主干原型种子、选型对照、改造原则
│   ├── playbooks.md           # 各原型打法手册：流程样板、抓手、留资插入点、物料分级、兜底
│   ├── proactive-playbook.md  # 主动推荐引擎与创意总监工作法：菜单三段式、提案卡、候选池
│   ├── cross-industry-playbook.md # 跨行业策略借鉴库：三档大胆度、分行业种子映射、排除清单
│   ├── contingency-playbook.md # 临场应变分支库：五组场景、六层接法、顺势加分动作
│   ├── plan-framework.md       # 第④⑤步：方案骨架、筹备倒排、当天 checklist、量力校验、降级预案
│   ├── lead-capture.md         # 第⑥步：两码分工、表单规格、跟进 SOP、归因映射、漏斗指标
│   ├── review-loop.md          # 第⑦⑧步：复盘三问、回流去向、分级规则
│   ├── red-lines.md            # 红线、事实检索、隐私合规与能力边界
│   ├── faq.md                  # 常见问题集中答疑
│   └── publish-checklist.md    # TRACE 五维发布前检查清单
├── tables/                     # 两张在线表字段骨架
│   ├── activity-archive.md     # 活动档案表（一场一行）
│   └── outreach-resource.md     # 外联资源库表（一场所一行）
├── examples/                   # 完整示例（演示口径，待核项占位）
│   ├── community-parent-child.md / .html
│   └── mall-pop-up.md / .html
├── scripts/
│   ├── scaffold_plan.py        # 生成骨架：single 方案卡 / manual 执行手册 / series 排期表 / resource 建档
│   ├── init_tables.py          # 初始化两张底座表：在线表之外的本地兜底（xlsx / md）
│   ├── render_html.py          # 方案卡 Markdown → 单文件 HTML
│   ├── check_plan.py           # 单文件结构校验与红线检测（.md / .html 双通道）
│   ├── check_deliverables.py   # 目录级产物齐套检查：方案卡 HTML/MD 底稿/执行手册缺件告警
│   └── selftest.py              # 冒烟测试用例
├── tests/
│   └── selftest-output.txt      # 最近一次自测与示例校验存档
└── agents/                      # 平台接口配置
```

## 三、安装与加载

1. 将本目录整体放入技能加载目录（或按所在平台的技能安装方式上传）。
2. 确认 `SKILL.md` 与 `scripts/`、`references/` 同级，目录结构未拆散。
3. 在对话中提到“招生活动、社区活动、探园日、体验课、异业合作、留资复盘、社区资源库”等即可触发；也可手动调用。
4. 脚本依赖 Python 3；核心脚本仅用标准库。生成本地 Excel 兜底表可选装 openpyxl，未装时自动降级为 Markdown 表结构，不影响主流程。

## 四、快速上手

**1. 看一份完整示例**

直接双击打开 `examples/*.html`，可离线阅读、Ctrl+P 打印或存 PDF；黄色高亮为待填/待核实处。

**2. 生成一份骨架**

```powershell
# 单场方案卡（默认出 HTML）
python scripts/scaffold_plan.py --title "社区亲子坊" --layer P1 --window 长期蓄水 --kind single --mode 走出去 --goal 留资

# 招生季排期表
python scripts/scaffold_plan.py --title "2027 春季排期" --window 春季 --kind series

# 外联资源建档
python scripts/scaffold_plan.py --title "某社区活动中心" --kind resource

# 有线下现场环节的单场，另出执行手册骨架（步骤 SOP＋当天 checklist＋速查表）
python scripts/scaffold_plan.py --title "社区亲子坊" --kind manual --mode 走出去 --layer P1 --window 长期蓄水 --goal 留资

# 初始化两张底座表（先试 Excel，缺 openpyxl 自动落 MD）
python scripts/init_tables.py --out ./tables_out

# 出纯文本底稿
python scripts/scaffold_plan.py --title "社区亲子坊" --format md
```

**3. 填充后自检**

```powershell
# 单文件结构校验 + 红线检测
python scripts/check_plan.py examples/<方案卡>.md

# 目录级产物齐套检查：方案卡 HTML/MD 底稿/执行手册是否缺件
python scripts/check_deliverables.py ./本场目录
```

退出码：0 通过（可含警告）；1 有错误；2 文件读取失败。线上蓄水/纯物料植入等无需手册的情形，在方案卡标注「手册豁免＋原因」即可跳过手册检查。

**4. 渲染 HTML**

```powershell
python scripts/render_html.py examples/<方案卡>.md -o examples/<方案卡>.html
```

## 五、自测

```powershell
python scripts/selftest.py
```

通过标准：全部用例通过；示例校验 0 错误；HTML 可离线打开。最近一次存档见 `tests/selftest-output.txt`。

## 六、双版口径

- **项目内版**：可保留项目背景与案例占位；已确认事实与待核实项分开标注，待核数字不写成事实。
- **公共发布版**：校名、班型名、社区案例、坐标、联系人、企业全称、具体户数/距离全部替换为通用示例；替换后按 `references/publish-checklist.md` 5.1 表逐项 grep 复检 0 残留。
