"""第 10 章：中间件洋葱模型 — 注册工具 → 中间件 → 洋葱式调用链"""
import asyncio
import time
from typing import AsyncGenerator, Callable

from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import ToolUseBlock, TextBlock


def echo(text: str) -> ToolResponse:
    """回显输入的文本。"""
    return ToolResponse(content=[TextBlock(type="text", text=f"echo: {text}")])


async def log_middleware(
    kwargs: dict, next_handler: Callable,
) -> AsyncGenerator[ToolResponse, None]:
    """外层：工具调用前后打印日志。"""
    tc = kwargs["tool_call"]
    print(f"  [LOG] before: {tc['name']}({tc['input']})")
    async for chunk in await next_handler(**kwargs):
        print(f"  [LOG] after:  {chunk.content[0].get('text', '')}")
        yield chunk


async def timing_middleware(
    kwargs: dict, next_handler: Callable,
) -> AsyncGenerator[ToolResponse, None]:
    """内层：测量工具执行耗时。"""
    t0 = time.perf_counter()
    async for chunk in await next_handler(**kwargs):
        print(f"  [TIME] {time.perf_counter() - t0:.4f}s")
        yield chunk


async def main() -> None:
    # → src/agentscope/tool/_toolkit.py:57 (_apply_middlewares 装饰器)
    # → src/agentscope/tool/_toolkit.py:1328 (register_agent_skill 方法)
    toolkit = Toolkit()
    toolkit.register_tool_function(echo)

    # 先注册的是外层，后注册的是内层
    toolkit.register_middleware(log_middleware)      # 外层
    toolkit.register_middleware(timing_middleware)    # 内层

    tool_call = ToolUseBlock(
        type="tool_use", id="call_001",
        name="echo", input={"text": "Hello Middleware"},
    )

    print("洋葱调用链: log → timing → echo → timing → log")
    gen = await toolkit.call_tool_function(tool_call)
    async for chunk in gen:
        for block in chunk.content:
            print(f"  [OUT] {block.get('text', '')}")


if __name__ == "__main__":
    asyncio.run(main())
