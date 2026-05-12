"""第 9 章：同步调用 vs 流式调用

展示一次性返回和逐 token 流式返回的区别。
切换 provider 只需改 .env 中的 LLM_PROVIDER。
"""
import asyncio

from config import get_model_and_formatter


async def main():
    model, _ = get_model_and_formatter()

    messages = [
        {"role": "user", "content": "用一句话介绍 Python 语言。"},
    ]

    # ── 同步调用：一次性返回完整结果 ──
    # → src/agentscope/model/_model_base.py  (ChatModelBase, __call__)
    # → src/agentscope/model/_openai_model.py  (stream handling)
    print("=" * 50)
    print("【同步调用】stream=False — 等待完整回复")
    print("=" * 50)
    response = await model(messages, stream=False)
    for block in response.content:
        if block.get("type") == "text":
            print(block["text"])
    print(f"\nUsage: {response.usage}")

    # ── 流式调用：逐 token 返回 ──
    # → src/agentscope/model/_openai_model.py  (_parse_openai_stream_response)
    print("\n" + "=" * 50)
    print("【流式调用】stream=True — 逐 token 逐字打印")
    print("=" * 50)
    async for chunk in model(messages, stream=True):
        for block in chunk.content:
            if block.get("type") == "text":
                print(block["text"], end="", flush=True)
    print()  # 换行收尾


if __name__ == "__main__":
    asyncio.run(main())
