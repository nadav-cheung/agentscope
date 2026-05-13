"""第 4 章：消息诞生 — Msg 和七种 ContentBlock

演示 AgentScope 消息（Msg）类型和内容块系统。
→ src/agentscope/message/_message_base.py:21   (Msg 类)
→ src/agentscope/message/_message_block.py:9    (ContentBlock 类型)
"""
from agentscope.message import (
    Msg, TextBlock, ImageBlock, AudioBlock, ThinkingBlock,
    ToolUseBlock, ToolResultBlock, URLSource,
)

# 1. TextBlock — 纯文本消息
# → src/agentscope/message/_message_block.py:9  (TextBlock 定义)
msg_text = Msg("user", "你好，世界！", "user")
print("=== TextBlock ===")
print(msg_text, "\n")

# 2. ImageBlock — 图片 URL 源
image_block = ImageBlock(
    type="image",
    source=URLSource(type="url", url="https://example.com/photo.jpg"),
)
print("=== ImageBlock ===")
print(Msg("user", [image_block], "user"), "\n")

# 3. ToolUseBlock — 模型请求调用工具
tool_use = ToolUseBlock(
    type="tool_use", id="call_001", name="get_weather",
    input={"city": "北京"},
)
print("=== ToolUseBlock ===")
print(Msg("assistant", [tool_use], "assistant"), "\n")

# 4. ToolResultBlock — 工具返回结果
tool_result = ToolResultBlock(
    type="tool_result", id="call_001", name="get_weather",
    output="晴，25°C，湿度30%",
)
print("=== ToolResultBlock ===")
print(Msg("user", [tool_result], "user"), "\n")

# 5. AudioBlock + ThinkingBlock — 多模态与推理
thinking = ThinkingBlock(type="thinking", thinking="我需要查询天气信息...")
audio = AudioBlock(
    type="audio",
    source=URLSource(type="url", url="https://example.com/audio.mp3"),
)
msg_multi = Msg("assistant", [thinking, audio], "assistant")
print("=== ThinkingBlock + AudioBlock ===")
print(f"thinking blocks: {msg_multi.get_content_blocks('thinking')}")
print(f"audio blocks:    {msg_multi.get_content_blocks('audio')}")
