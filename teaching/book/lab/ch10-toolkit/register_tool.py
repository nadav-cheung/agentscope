"""第 10 章：工具注册与执行

演示: 定义函数 → 注册到 Toolkit → 构造 ToolUseBlock → 执行 → ToolResponse
"""
import asyncio

from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import ToolUseBlock, TextBlock


def calculator(operation: str, a: float, b: float) -> ToolResponse:
    """基本算术运算，支持 add / subtract。"""
    if operation == "add":
        result, symbol = a + b, "+"
    elif operation == "subtract":
        result, symbol = a - b, "-"
    else:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"不支持的运算: {operation}")],
        )
    return ToolResponse(
        content=[TextBlock(type="text", text=f"{a} {symbol} {b} = {result}")],
    )


async def main() -> None:
    # → src/agentscope/tool/_toolkit.py:1284 (register_tool_function)
    # → src/agentscope/tool/_response.py (ToolResponse)
    # → src/agentscope/tool/_types.py (ToolFunction, ToolUseBlock)
    toolkit = Toolkit()
    toolkit.register_tool_function(calculator)

    print("已注册工具:", list(toolkit.tools.keys()))
    schema = toolkit.tools["calculator"].json_schema
    print("工具描述:", schema["function"]["description"])

    # 手工构造 ToolUseBlock — 模拟 LLM 返回的 tool_use 块
    tool_call = ToolUseBlock(
        type="tool_use",
        id="call_001",
        name="calculator",
        input={"operation": "add", "a": 3, "b": 5},
    )
    print(f"\n调用工具: {tool_call['name']}({tool_call['input']})")

    # 执行工具，异步迭代结果
    tool_res = toolkit.call_tool_function(tool_call)
    async for chunk in tool_res:
        for block in chunk.content:
            print(f"工具结果: {block.get('text', '')}")


if __name__ == "__main__":
    asyncio.run(main())
