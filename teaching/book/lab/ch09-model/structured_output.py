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
    # → src/agentscope/model/_openai_model.py  (_structured_via_tool_call)
    # → src/agentscope/model/_model_base.py  (structured_output support)
    print("【结构化输出】传入 structured_model=UserInfo")
    print("-" * 40)
    response = await model(messages, structured_model=UserInfo, stream=False)

    if response.metadata:
        print(f"name: {response.metadata['name']}")
        print(f"age:  {response.metadata['age']}")
    else:
        # 部分 provider 可能不返回 metadata，兜底打印文本
        for block in response.content:
            if block.get("type") == "text":
                print(block["text"])


if __name__ == "__main__":
    asyncio.run(main())
