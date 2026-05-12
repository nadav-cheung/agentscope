"""第 27 章：高级扩展 — Agent Skill

Agent Skill = 提示词 + 工具 + 文件 打包为可复用单元

目录结构:
  skills/code-review/
  ├── SKILL.md          (YAML 头部: name + description)
  └── instructions.md   (提示词模板)

注册: toolkit.register_agent_skill("./skills/code-review/")
  → 解析 SKILL.md → 存入 skills 字典 → get_agent_skill_prompt() 注入
"""
import tempfile
import os

from agentscope.tool import Toolkit

# → src/agentscope/tool/_toolkit.py:1328 (register_agent_skill)
# → src/agentscope/tool/_toolkit.py:187  (create_tool_group)


def main() -> None:
    with tempfile.TemporaryDirectory() as skill_dir:
        # 编写 SKILL.md (必须有 YAML Front Matter 的 name + description)
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write("""---
name: code-review
description: Review Python code for bugs, style, and security issues.
---

# Code Review Skill

1. Read the code carefully.
2. Check for bugs, edge cases, resource leaks.
3. Report findings as structured output.
""")

        toolkit = Toolkit()
        print(f"[1] Skill 目录: {skill_dir}")

        toolkit.register_agent_skill(skill_dir)
        print(f"[2] 已注册: {list(toolkit.skills.keys())}")
        print(f"    name: {toolkit.skills['code-review']['name']}")

        prompt = toolkit.get_agent_skill_prompt()
        print(f"[3] Agent 提示词(可注入 sys_prompt):\n    {prompt[:150]}...")


if __name__ == "__main__":
    main()
