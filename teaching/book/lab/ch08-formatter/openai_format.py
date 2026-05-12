"""第 8 章附录：OpenAI 消息格式化

演示 Msg → OpenAI API dict 的转换过程。
→ src/agentscope/formatter/_formatter_base.py  (FormatterBase)
→ src/agentscope/formatter/_openai_formatter.py (OpenAIChatFormatter)
"""
import asyncio
import json

from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg, TextBlock, ToolUseBlock, ToolResultBlock


async def main():
    # 1. 创建示例消息
    # → src/agentscope/message/_message_base.py (Msg 类)
    msgs = [
        Msg("user", "北京今天天气怎么样？", "user"),
        Msg("assistant", [
            TextBlock(type="text", text="好的，我来帮你查天气。"),
            ToolUseBlock(
                type="tool_use",
                id="call_001",
                name="get_weather",
                input={"city": "北京"},
            ),
        ], "assistant"),
        Msg("system", [
            ToolResultBlock(
                type="tool_result",
                id="call_001",
                name="get_weather",
                output="晴，25°C，湿度30%",
            ),
        ], "system"),
    ]

    # 2. 格式化
    # → src/agentscope/formatter/_openai_formatter.py:219 (_format)
    formatter = OpenAIChatFormatter()
    formatted = await formatter.format(msgs)

    # 3. 输出 OpenAI 结构
    print("=" * 60)
    print("OpenAI API 消息格式")
    print("=" * 60)
    print(json.dumps(formatted, ensure_ascii=False, indent=2))

    # 4. 关键结构说明
    print("\n" + "=" * 60)
    print("关键点:")
    print("  - tool_use  → msg['tool_calls'][*]{id, type:'function', function}")
    print("  - tool_result → 独立消息 {role:'tool', tool_call_id, content}")


if __name__ == "__main__":
    asyncio.run(main())
