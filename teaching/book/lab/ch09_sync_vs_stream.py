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

    # ── 收集模式：等所有 chunk 到齐后一次打印 ──
    # → src/agentscope/model/_openai_model.py:176  (OpenAIChatModel.__call__)
    # 追踪中间件包裹后，需先 await 再 async for
    print("=" * 50)
    print("【收集模式】收集所有流式 chunk 后一次打印")
    print("=" * 50)
    full_text = ""
    stream = await model(messages)
    async for chunk in stream:
        for block in chunk.content:
            if block.get("type") == "text":
                full_text = block["text"]
    print(full_text)

    # ── 流式模式：逐 token 即时打印 ──
    print("\n" + "=" * 50)
    print("【流式模式】逐 token 即时打印")
    print("=" * 50)
    stream = await model(messages)
    prev_text = ""
    async for chunk in stream:
        for block in chunk.content:
            if block.get("type") == "text":
                # 提取增量（兼容累积式流式返回）
                delta = block["text"][len(prev_text):]
                print(delta, end="", flush=True)
                prev_text = block["text"]
    print()  # 换行收尾


if __name__ == "__main__":
    asyncio.run(main())
