#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把招生活动方案卡 Markdown 渲染成单文件 HTML（A4 打印友好 + 屏幕阅读舒适）。

用法：
    python render_html.py 方案卡.md
    python render_html.py 方案卡.md -o 输出.html

生成的 HTML 不依赖任何外部资源，双击即可打开，也可直接 Ctrl+P 打印或存 PDF。
"""

import argparse
import html
import os
import re
import sys


# ---------- 行内处理 ----------

def inline(text):
    """转义 + 行内加粗 + 【待填/待核实】高亮"""
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"【(待填[^】]*)】", r'<span class="todo">【\1】</span>', t)
    t = re.sub(r"【(待核实[^】]*)】", r'<span class="todo">【\1】</span>', t)
    return t


# ---------- 解析 ----------

def parse(md):
    title = None
    meta = []
    sections = []
    cur = None

    for raw in md.splitlines():
        line = raw.rstrip()
        if title is None and line.startswith("# "):
            title = line[2:].strip()
            continue
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            name = re.sub(r"^[一二三四五六七八九十]+\s*、\s*", "", m.group(1)).strip()
            cur = [name, []]
            sections.append(cur)
            continue
        if cur is None:
            if not line.strip():
                continue
            for k, v in re.findall(r"\*\*(.+?)\*\*[：:]\s*([^　]*)", line):
                meta.append((k.strip(), v.strip()))
            continue
        cur[1].append(line)

    return (title or "招生活动方案卡"), meta, sections


# ---------- 章节渲染 ----------

def render_table(lines):
    rows = [l.strip() for l in lines if l.strip().startswith("|")]
    data = []
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if all(re.match(r"^[-: ]*$", c) for c in cells):
            continue
        data.append(cells)
    if not data:
        return '<p class="muted">（未填写）</p>'
    head, body = data[0], data[1:]
    th = "".join(f"<th>{inline(c)}</th>" for c in head)
    trs = "".join(
        "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>"
        for row in body
    )
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def render_list(lines):
    """按行序渲染：列表项进 ul，普通段落进 p，三级标题进 h3；不在列表时丢弃段落。"""
    out, items = [], []

    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            items.clear()

    for l in lines:
        if not l.strip():
            continue
        h3 = re.match(r"^\s*###\s+(.*)$", l)
        m = re.match(r"^\s*(?:\d+[.、]\s*|-\s+|\*\s+)(.*)$", l)
        if h3:
            flush()
            out.append(f"<h3>{inline(h3.group(1).strip())}</h3>")
        elif m and m.group(1).strip():
            items.append(m.group(1).strip())
        else:
            flush()
            out.append(f"<p>{inline(re.sub(r'^\\s*-\\s*', '', l).strip())}</p>")
    flush()
    return "".join(out) or '<p class="muted">（未填写）</p>'


def split_blocks(lines):
    """按行序把一章切成有序块：连续表格行成一个 table 块，其余成 text 块。"""
    blocks = []
    cur_kind, cur = None, []

    def flush():
        nonlocal cur_kind, cur
        if cur:
            # 纯空行形成的 text 块直接丢弃，避免表格前后冒出“（未填写）”占位
            if cur_kind == "table" or any(x.strip() for x in cur):
                blocks.append((cur_kind, cur))
            cur = []

    for l in lines:
        kind = "table" if l.strip().startswith("|") else "text"
        if cur_kind is None:
            cur_kind = kind
        if kind != cur_kind:
            flush()
            cur_kind = kind
        cur.append(l)
    flush()
    return blocks


def render_section(name, lines):
    out = []
    for kind, block in split_blocks(lines):
        out.append(render_table(block) if kind == "table" else render_list(block))
    return "".join(out)


# ---------- 整页模板 ----------

CSS = """
:root{
  --wf-red:#9B1C2C; --wf-red-deep:#7A1420; --wf-gold:#C9A227; --wf-gold-deep:#8A6D1A;
  --wf-paper:#FAF6EE; --wf-ink:#2B2620; --wf-gray:#6B5F52; --line:#ddd3c4;
  --todo:#fff3c4;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:#eee9df; color:var(--wf-ink);
  font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Source Han Sans SC",sans-serif;
  font-size:15px; line-height:1.75; -webkit-font-smoothing:antialiased;
}
.toolbar{max-width:210mm;margin:18px auto 0;text-align:right}
.toolbar button{
  font:inherit;font-size:14px;padding:8px 18px;border-radius:6px;border:1px solid var(--line);
  background:#fff;color:var(--wf-ink);cursor:pointer
}
.toolbar button:hover{border-color:var(--wf-red);color:var(--wf-red)}
.sheet{
  max-width:210mm;margin:14px auto 40px;background:#fff;
  padding:16mm 15mm 18mm;box-shadow:0 6px 24px rgba(60,45,25,.12);border-radius:2px;
  border-top:4px solid var(--wf-red);
}
.eyebrow{font-size:12.5px;letter-spacing:.18em;color:var(--wf-gray);margin-bottom:6px}
h1{font-family:Georgia,"Noto Serif SC","Source Han Serif SC",serif;font-size:26px;line-height:1.35;margin:0 0 10px;padding-bottom:10px;border-bottom:2px solid var(--wf-gold)}
.meta{display:flex;flex-wrap:wrap;gap:9px 24px;margin:0 0 4px;padding:0;font-size:14px;color:var(--wf-ink)}
.meta span{display:inline-flex;align-items:baseline}
.meta span strong{color:var(--wf-gray);font-weight:500;margin-right:7px;flex:0 0 auto}
section{margin-top:22px}
h2{font-family:Georgia,"Noto Serif SC","Source Han Serif SC",serif;font-size:17px;margin:0 0 12px;display:flex;align-items:center;gap:9px;color:var(--wf-red-deep)}
h2::before{content:"";width:4px;height:16px;background:var(--wf-gold);border-radius:2px;display:inline-block}
h3{font-size:15px;margin:12px 0 6px;color:var(--wf-red-deep)}
ul{margin:0;padding-left:0;list-style:none}
ul li{position:relative;padding-left:17px;margin:5px 0}
ul li::before{content:"";position:absolute;left:2px;top:11px;width:5px;height:5px;border-radius:50%;background:var(--wf-gold)}
.table-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
.table-wrap table{min-width:460px}
table{width:100%;border-collapse:collapse;font-size:14px;break-inside:avoid;page-break-inside:avoid}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--wf-paper);font-weight:600;color:var(--wf-red-deep)}
tbody tr:nth-child(even){background:#fcfaf5}
.muted{color:var(--wf-gray)}
.todo{background:var(--todo);border-radius:3px;padding:0 2px}
footer{margin-top:26px;padding-top:10px;border-top:1px solid var(--line);font-size:12.5px;color:var(--wf-gray);display:flex;justify-content:space-between}
@media print{
  @page{size:A4;margin:12mm 12mm 12mm}
  body{background:#fff;font-size:13.5px;line-height:1.62}
  .toolbar{display:none}
  .sheet{box-shadow:none;margin:0;padding:0;max-width:none;border-top-width:3px}
  .eyebrow{font-size:11px;margin-bottom:3px}
  h1{font-size:21px;margin-bottom:7px;padding-bottom:7px}
  .meta{font-size:12.5px;gap:5px 16px}
  section{margin-top:13px}
  h2{font-size:15px;margin-bottom:7px}
  table{font-size:12.5px}
  .table-wrap{overflow:visible}
  .table-wrap table{min-width:0}
  th,td{padding:5px 8px}
  footer{margin-top:14px;padding-top:7px}
}
@media (max-width:720px){
  .sheet{padding:20px 16px;margin:0;border-radius:0}
  h1{font-size:21px}
  .meta{font-size:13px}
}
"""


def build_html(title, meta, sections):
    meta_html = "".join(
        f"<span><strong>{html.escape(k)}</strong>{inline(v)}</span>" for k, v in meta
    )
    body = []
    for name, lines in sections:
        body.append(f"<section><h2>{html.escape(name)}</h2>{render_section(name, lines)}</section>")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · 招生活动方案卡</title>
<style>{CSS}</style>
</head>
<body>
<div class="toolbar"><button onclick="window.print()">打印 / 存 PDF</button></div>
<main class="sheet">
  <header>
    <div class="eyebrow">幼儿园招生活动工作台 · 方案卡</div>
    <h1>{html.escape(title)}</h1>
    <div class="meta">{meta_html}</div>
  </header>
  {''.join(body)}
  <footer>
    <span>幼儿园招生活动工作台</span>
    <span>打印建议：A4 纵向，页边距选"默认"</span>
  </footer>
</main>
</body>
</html>
"""


def render_markdown(md_text):
    title, meta, sections = parse(md_text)
    return build_html(title, meta, sections)


def main():
    ap = argparse.ArgumentParser(description="把招生活动方案卡 Markdown 渲染为单文件 HTML")
    ap.add_argument("path", help="方案卡 Markdown 文件")
    ap.add_argument("-o", "--out", default=None, help="输出 HTML 路径（默认同名 .html）")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"[错误] 文件不存在：{args.path}", file=sys.stderr)
        return 2
    if os.path.isdir(args.path):
        print(f"[错误] 传入的是文件夹，请指定具体的 Markdown 文件：{args.path}", file=sys.stderr)
        return 2

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            md = f.read()
    except UnicodeDecodeError:
        print("[错误] 文件编码无法识别，请另存为 UTF-8 编码后再渲染", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"[错误] 文件读取失败：{e}", file=sys.stderr)
        return 2

    if not md.strip():
        print("[错误] 文件内容为空，请先填写方案卡再渲染", file=sys.stderr)
        return 2

    try:
        doc = render_markdown(md)
        out = args.out or os.path.splitext(args.path)[0] + ".html"
        out_dir = os.path.dirname(os.path.abspath(out))
        os.makedirs(out_dir, exist_ok=True)
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(doc)
        except OSError:
            # 写入失败回滚：删掉可能已产生的半截文件，避免留下损坏产物
            if os.path.exists(out):
                try:
                    os.remove(out)
                except OSError:
                    pass
            raise
    except OSError as e:
        print(f"[错误] 输出文件写入失败：{e}", file=sys.stderr)
        return 2

    print(f"[完成] 已生成 HTML：{out}")
    print(f"[提示] 双击打开即可阅读，Ctrl+P 可直接打印或存 PDF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
