"""第 1 章：什么是大模型（LLM）

跑通第一行代码——用 AgentScope 调用 LLM。
使用 config.py 的三 provider 切换机制。
"""
import asyncio

from config import get_model_and_formatter

# → src/agentscope/model/_openai_model.py:176  (OpenAIChatModel.__call__)
# → src/agentscope/model/_model_base.py:38      (ChatModelBase 抽象方法)


async def main():
    model, _formatter = get_model_and_formatter()

    messages = [
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "什么是大语言模型？用一句话回答。"},
    ]

    # 调用模型（追踪中间件包裹后需 await → async for）
    stream = await model(messages)
    full_text = ""
    async for chunk in stream:
        for block in chunk.content:
            if block.get("type") == "text":
                full_text = block["text"]
    print("模型回复:")
    print(full_text)


if __name__ == "__main__":
    asyncio.run(main())
