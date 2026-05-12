"""第 28 章：集成实战 — 将所有自定义组件组装为完整 Agent

卷三收官: 串联前几章的自定义组件:
  ch22 自定义工具 → ch23 自定义模型 → ch24 自定义记忆
  → ch25 自定义 Agent → ch26 MCP 集成 → ch27 中间件 & Skill
"""
import asyncio

from agentscope.memory import InMemoryMemory
from agentscope.message import Msg, TextBlock
from agentscope.tool import Toolkit, ToolResponse

# → src/agentscope/tool/       (ch22: 自定义工具)
# → src/agentscope/memory/     (ch24: 自定义记忆)
# → src/agentscope/agent/      (ch25: 自定义 Agent)
# → src/agentscope/model/      (ch23: 自定义模型)
# → src/agentscope/formatter/  (消息格式化)
# → src/agentscope/mcp/        (ch26: MCP 集成)
# → src/agentscope/tool/_toolkit.py (ch27: 中间件 & Skill)


# ── 组件 1: 日志工具 (ch22 模式) ──
def log_tool(message: str) -> ToolResponse:
    """记录日志。"""
    print(f"  [LOG] {message}")
    return ToolResponse(
        content=[TextBlock(type="text", text=f"已记录: {message}")],
    )


# ── 组件 2: 标签记忆 (ch24 模式, 继承 InMemoryMemory) ──
class TaggedMemory(InMemoryMemory):
    """带标签过滤的记忆。"""

    async def get_by_tag(self, tag: str) -> list[Msg]:
        return [msg for msg, _marks in self.content if msg.metadata.get("tag") == tag]


async def main() -> None:
    print("=" * 55)
    print("卷三收官: 自定义组件大串联")
    print("=" * 55)

    # 1. 工具 (ch22 + ch27 中间件 + ch26 MCP)
    toolkit = Toolkit()
    toolkit.register_tool_function(log_tool)
    print(f"\n[工具] 已注册: {list(toolkit.tools.keys())}")

    # 2. 记忆 (ch24)
    memory = TaggedMemory()
    print("[记忆] TaggedMemory (扩展 InMemoryMemory)")

    # 3. 架构一览
    print("\n[架构] 完整 Agent 组件关系:")
    print("  ┌────────────────────────────────┐")
    print("  │         Custom Agent           │")
    print("  │  model      ← ch23 自定义模型  │")
    print("  │  formatter  ← ch08 格式化器    │")
    print("  │  toolkit    ← ch22+ch26+ch27   │")
    print("  │  memory     ← ch24 自定义记忆  │")
    print("  └────────────────────────────────┘")

    # 4. 演示: 工具调用
    result = log_tool("集成测试启动")
    print(f"\n[运行] 工具输出: {result.content[0]['text']}")

    # 5. 记忆操作
    msg = Msg("user", "测试消息", "user", metadata={"tag": "test"})
    await memory.add(msg)
    tagged = await memory.get_by_tag("test")
    print(f"[记忆] 存储 {len(memory.content)} 条, tag='test' 匹配 {len(tagged)} 条")

    print("\n" + "=" * 55)
    print("集成完成! 已走完「使用框架 → 扩展框架」的完整路径。")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
