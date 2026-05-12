"""第 4 章：消息序列化 — to_dict / from_dict

演示 AgentScope Msg 的序列化与反序列化。
→ src/agentscope/message/_message_base.py (to_dict/from_dict 方法)
"""
from agentscope.message import Msg, TextBlock, ToolUseBlock

# 创建一条包含多个 ContentBlock 的消息
original = Msg(
    name="assistant",
    content=[
        TextBlock(type="text", text="我需要调用工具。"),
        ToolUseBlock(
            type="tool_use", id="call_42", name="get_weather",
            input={"city": "上海"},
        ),
    ],
    role="assistant",
    metadata={"source": "react_loop"},
)
print("=== 原始 Msg ===")
print(original, "\n")

# 序列化：Msg → dict
# → src/agentscope/message/_message_base.py:75 (to_dict)
d = original.to_dict()
print("=== to_dict() ===")
print(f"keys: {list(d.keys())}")
print(f"content: {d['content']}")
print(f"metadata: {d['metadata']}\n")

# 反序列化：dict → Msg
# → src/agentscope/message/_message_base.py:86 (from_dict)
restored = Msg.from_dict(d)
print("=== from_dict() ===")
print(restored, "\n")

# 验证往返一致性
assert original.name == restored.name
assert original.role == restored.role
assert original.content == restored.content
assert original.metadata == restored.metadata
print("✓ 往返一致：original.content == restored.content")
