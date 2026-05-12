#!/usr/bin/env python3
"""Add prev/next navigation links to all book chapters."""

import os
import sys

BOOK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chapter sequence: (volume_dir, filename, chapter_title_for_link)
CHAPTERS = [
    ("volume-0-basics", "ch01-what-is-llm.md", "第 1 章 什么是大模型（LLM）"),
    ("volume-0-basics", "ch02-what-is-agent.md", "第 2 章 什么是 Agent"),
    ("volume-1-journey", "ch03-toolbox.md", "第 3 章 准备工具箱"),
    ("volume-1-journey", "ch04-message-born.md", "第 4 章 第 1 站：消息诞生"),
    ("volume-1-journey", "ch05-agent-receives.md", "第 5 章 第 2 站：Agent 收信"),
    ("volume-1-journey", "ch06-memory-store.md", "第 6 章 第 3 站：工作记忆"),
    ("volume-1-journey", "ch07-retrieval-knowledge.md", "第 7 站：检索与知识"),
    ("volume-1-journey", "ch08-formatter.md", "第 8 站：格式转换"),
    ("volume-1-journey", "ch09-model.md", "第 9 站：调用模型"),
    ("volume-1-journey", "ch10-toolkit.md", "第 10 站：执行工具"),
    ("volume-1-journey", "ch11-loop-return.md", "第 11 站：循环与返回"),
    ("volume-1-journey", "ch12-journey-review.md", "旅程复盘"),
    ("volume-2-patterns", "ch13-module-system.md", "第 13 章 模块系统"),
    ("volume-2-patterns", "ch14-inheritance.md", "第 14 章 继承体系"),
    ("volume-2-patterns", "ch15-metaclass-hooks.md", "第 15 章 元类与 Hook"),
    ("volume-2-patterns", "ch16-formatter-strategy.md", "第 16 章 策略模式"),
    ("volume-2-patterns", "ch17-schema-factory.md", "第 17 章 工厂与 Schema"),
    ("volume-2-patterns", "ch18-middleware.md", "第 18 章 中间件与洋葱模型"),
    ("volume-2-patterns", "ch19-pubsub.md", "第 19 章 发布-订阅"),
    ("volume-2-patterns", "ch20-observability.md", "第 20 章 可观测性与持久化"),
    ("volume-3-building", "ch21-dev-setup.md", "第 21 章 扩展准备"),
    ("volume-3-building", "ch22-new-tool.md", "第 22 章 造一个新 Tool"),
    ("volume-3-building", "ch23-new-model.md", "第 23 章 造一个新 Model Provider"),
    ("volume-3-building", "ch24-new-memory.md", "第 24 章 造一个新 Memory Backend"),
    ("volume-3-building", "ch25-new-agent.md", "第 25 章 造一个新 Agent 类型"),
    ("volume-3-building", "ch26-mcp-server.md", "第 26 章 集成 MCP Server"),
    ("volume-3-building", "ch27-advanced-extension.md", "第 27 章 高级扩展"),
    ("volume-3-building", "ch28-integration-capstone.md", "第 28 章 终章——集成实战"),
    ("volume-4-why", "ch29-msg-interface.md", "第 29 章 消息为什么是唯一接口"),
    ("volume-4-why", "ch30-no-decorator.md", "第 30 章 为什么不用装饰器注册工具"),
    ("volume-4-why", "ch31-god-class.md", "第 31 章 上帝类 vs 模块拆分"),
    ("volume-4-why", "ch32-compile-time-hooks.md", "第 32 章 编译期 Hook vs 运行时 Hook"),
    ("volume-4-why", "ch33-typedict-union.md", "第 33 章 为什么 ContentBlock 是 TypedDict Union"),
    ("volume-4-why", "ch34-contextvar.md", "第 34 章 为什么用 ContextVar"),
    ("volume-4-why", "ch35-formatter-separate.md", "第 35 章 为什么 Formatter 独立于 Model"),
    ("volume-4-why", "ch36-panorama.md", "第 36 章 架构全景与边界"),
    ("appendix", "python-primer.md", "附录 A：Python 进阶速查"),
    ("appendix", "glossary.md", "附录 B：术语表"),
    ("appendix", "source-map.md", "附录 C：源码地图"),
]


def add_prev_link(lines, vol_dir, i):
    """Insert prev-chapter link after the title block. Returns (lines, changed)."""
    if i == 0:
        return lines, False  # First chapter, no prev link

    prev_vol, prev_file, prev_title = CHAPTERS[i - 1]
    rel_path = f"./{prev_file}" if vol_dir == prev_vol else f"../{prev_vol}/{prev_file}"
    link_line = f"> **上一章：[{prev_title}]({rel_path})**"

    # Check if already has a prev link
    for line in lines:
        if "> **上一章：" in line:
            return lines, False

    # Find the title line
    title_idx = None
    for j, line in enumerate(lines):
        if line.startswith("# ") and not line.startswith("## "):
            title_idx = j
            break

    if title_idx is None:
        return lines, False

    # Skip title, then blank lines
    j = title_idx + 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1

    # Skip the first content block (blockquote or paragraph)
    if j < len(lines) and lines[j].startswith(">"):
        while j < len(lines) and lines[j].startswith(">"):
            j += 1
    else:
        while j < len(lines) and lines[j].strip() != "" and not lines[j].startswith("---") and not lines[j].startswith("## "):
            j += 1

    # Skip blank lines after the content block
    while j < len(lines) and lines[j].strip() == "":
        j += 1

    # Insert prev link with a blank line before it, at position j
    lines.insert(j, "")
    lines.insert(j, link_line)
    return lines, True


def add_next_link(lines, vol_dir, i):
    """Append next-chapter link at the end. Returns (lines, changed)."""
    if i >= len(CHAPTERS) - 1:
        return lines, False  # Last chapter, no next link

    next_vol, next_file, next_title = CHAPTERS[i + 1]
    rel_path = f"./{next_file}" if vol_dir == next_vol else f"../{next_vol}/{next_file}"
    link_line = f"> **下一章：[{next_title}]({rel_path})**"

    # Check if already has a clickable next link to this specific chapter
    for line in lines:
        if f"[{next_title}]" in line:
            return lines, False

    # Append at the very end, with a blank line separator
    if lines[-1].strip() != "":
        lines.append("")
    lines.append(link_line)
    return lines, True


def main():
    changes = []
    for i, (vol_dir, filename, title) in enumerate(CHAPTERS):
        filepath = os.path.join(BOOK_DIR, vol_dir, filename)
        if not os.path.exists(filepath):
            print(f"SKIP (not found): {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        changed = False

        lines, c1 = add_prev_link(lines, vol_dir, i)
        changed = changed or c1

        lines, c2 = add_next_link(lines, vol_dir, i)
        changed = changed or c2

        if changed:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            changes.append(f"{vol_dir}/{filename}")
        else:
            print(f"NO CHANGE: {vol_dir}/{filename}")

    print(f"\nModified {len(changes)} files:")
    for c in changes:
        print(f"  {c}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
