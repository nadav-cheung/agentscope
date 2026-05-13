"""第 9 章：结构化输出

让 LLM 返回符合指定 JSON Schema 的结构化数据。
通过 tool-call 机制强迫模型输出可解析的 JSON。
"""
import asyncio

from pydantic import BaseModel

from config import get_model_and_formatter


class UserInfo(BaseModel):
    """用户信息结构 — 模型会按此 schema 返回数据"""

    name: str
    age: int


async def main():
    model, _ = get_model_and_formatter()

    messages = [
        {"role": "user", "content": "张三今年 28 岁，请提取他的信息。"},
    ]

    # ── 结构化输出 ──
    # → src/agentscope/model/_openai_model.py:730  (_structured_via_tool_call)
    # → src/agentscope/model/_model_base.py:38      (ChatModelBase 抽象方法)
    print("【结构化输出】传入 structured_model=UserInfo")
    print("-" * 40)
    # 收集所有 chunk（追踪中间件包裹后需先 await）
    full_text = ""
    last_metadata = None
    stream = await model(messages, structured_model=UserInfo)
    async for chunk in stream:
        for block in chunk.content:
            if block.get("type") == "text":
                full_text = block["text"]
        if chunk.metadata:
            last_metadata = chunk.metadata

    if last_metadata:
        print(f"name: {last_metadata.get('name', 'N/A')}")
        print(f"age:  {last_metadata.get('age', 'N/A')}")
    else:
        print(full_text)


if __name__ == "__main__":
    asyncio.run(main())
