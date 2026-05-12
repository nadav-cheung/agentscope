"""第 1 章：什么是大模型（LLM）

跑通第一行代码——用 AgentScope 调用 LLM。
切换 provider 只需改 .env 中的 LLM_PROVIDER。
"""
from agentscope.model import OpenAIChatModel

# 最简单的 LLM 调用：构造 model，发消息，收回复
# → src/agentscope/model/_openai_model.py  (OpenAIChatModel 实现)
# → src/agentscope/model/_model_base.py    (ChatModelBase 基类)

model = OpenAIChatModel(
    model_name="deepseek-chat",
    api_key="your-api-key",  # 替换为你的 API key
    base_url="https://api.deepseek.com/v1",
)

# 消息格式：role + content
messages = [
    {"role": "system", "content": "你是一个有帮助的助手。"},
    {"role": "user", "content": "什么是大语言模型？用一句话回答。"},
]

response = model(messages)
print("模型回复:")
print(response.text)
print(f"\nToken 用量: {response.usage}")
