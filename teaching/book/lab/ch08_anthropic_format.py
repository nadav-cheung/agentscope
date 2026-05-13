"""第 8 章附录：Anthropic vs OpenAI 格式对比

并列展示同一组 Msg 经两个 formatter 转换后的结构差异。
→ src/agentscope/formatter/_anthropic_formatter.py:98       (AnthropicChatFormatter)
→ src/agentscope/formatter/_truncated_formatter_base.py:19  (TruncatedFormatterBase)
"""
import asyncio
import json

from agentscope.formatter import (
    AnthropicChatFormatter,
    OpenAIChatFormatter,
)
from agentscope.message import Msg, TextBlock, ToolUseBlock, ToolResultBlock


async def main():
    # 同样的消息，两种格式
    msgs = [
        Msg("user", "北京今天天气怎么样？", "user"),
        Msg("assistant", [
            TextBlock(type="text", text="我来查一下天气。"),
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
                output="晴，25°C",
            ),
        ], "system"),
    ]

    # 分别格式化
    openai_out = await OpenAIChatFormatter().format(msgs)
    anthropic_out = await AnthropicChatFormatter().format(msgs)

    # 并排输出
    print("=" * 70)
    print(f"{'OpenAI 格式':<34} │ {'Anthropic 格式'}")
    print("=" * 70)
    print(f"{json.dumps(openai_out, ensure_ascii=False, indent=5):<34} │ "
          f"{json.dumps(anthropic_out, ensure_ascii=False, indent=5)}")

    # 差异总结
    print("\n" + "=" * 70)
    print("结构差异:")
    print("  OpenAI:  tool_use→msg['tool_calls']; tool_result→{role:'tool'}")
    print("  Anthropic: tool_use→content block; tool_result→{role:'user', content}")


if __name__ == "__main__":
    asyncio.run(main())
