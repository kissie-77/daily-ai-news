#!/usr/bin/env python3
"""根据所有 morning.md 重建首页 README。

规则（见交接文档）：
- 只根据 `YYYY/MM/YYYY-MM-DD/morning.md` 生成，不要手改 README
- 条数按文件内的 `## N. 标题` 统计
- 按月折叠，生成「日期 | 当日新闻」表
- 在仓库根目录运行：python3 scripts/build_readme.py
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TITLE_RE = re.compile(r"^##\s+\d+\.\s+(.+?)\s*$", re.MULTILINE)
DATE_RE = re.compile(r"^(\d{4})/(\d{2})/(\d{4})-(\d{2})-(\d{2})/morning\.md$")


def collect():
    """返回 {month: [(date, rel_path, [titles])]}，按日期倒序。"""
    by_month: dict[str, list] = defaultdict(list)
    for path in sorted(ROOT.glob("20*/*/20*-*/morning.md")):
        rel = path.relative_to(ROOT).as_posix()
        m = DATE_RE.match(rel)
        if not m:
            continue
        year, month, y2, mo, day = m.groups()
        if (year, month) != (y2, mo):
            continue
        date = f"{y2}-{mo}-{day}"
        text = path.read_text(encoding="utf-8", errors="ignore")
        titles = [t.strip() for t in TITLE_RE.findall(text) if t.strip()]
        by_month[f"{year}-{month}"].append((date, rel, titles))
    for month in by_month:
        by_month[month].sort(reverse=True)
    return dict(sorted(by_month.items(), reverse=True))


def render(by_month):
    total_days = sum(len(v) for v in by_month.values())
    total_items = sum(len(titles) for v in by_month.values() for _, _, titles in v)
    lines = [
        "# 每日 AI 事件",
        "",
        "> 每天收录当天最热的 AI 新闻（模型、产品、融资、政策、研究，国内外混合），摘要为自行整理，详情请以原文为准。",
        ">",
        "> 更新时间：每天北京时间 10:00 左右（每周随机跳过 1 天）。",
        "",
        f"目前共收录 **{total_days}** 天、**{total_items}** 条新闻。",
        "",
        "## 目录",
        "",
    ]
    if not by_month:
        lines += ["暂无内容，首次更新后这里会自动生成按月目录。", ""]
        return "\n".join(lines)

    for month, days in by_month.items():
        month_total = sum(len(t) for _, _, t in days)
        lines += [
            f"<details open>",
            f"<summary><strong>{month}</strong>（{len(days)} 天，{month_total} 条）</summary>",
            "",
            "| 日期 | 条数 | 当日新闻 |",
            "| --- | ---: | --- |",
        ]
        for date, rel, titles in days:
            joined = "；".join(titles) if titles else "—"
            # 表格里避免 | 破坏列
            joined = joined.replace("|", "｜")
            lines.append(f"| [{date}]({rel}) | {len(titles)} | {joined} |")
        lines += ["", "</details>", ""]
    return "\n".join(lines)


def main():
    by_month = collect()
    readme = render(by_month)
    if not readme.endswith("\n"):
        readme += "\n"
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"README rebuilt: {sum(len(v) for v in by_month.values())} days, "
          f"{sum(len(t) for v in by_month.values() for _, _, t in v)} items")


if __name__ == "__main__":
    main()
