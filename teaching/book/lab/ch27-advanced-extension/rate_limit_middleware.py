"""第 27 章：高级扩展 — 自定义限流中间件

中间件洋葱模型:
  请求 → mid_1 前置 → mid_2 前置 → 执行工具 → mid_2 后置 → mid_1 后置
"""
import asyncio
import time

from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock, ToolUseBlock

# → src/agentscope/tool/_toolkit.py:57   (_apply_middlewares)
# → src/agentscope/tool/_toolkit.py:1441 (register_middleware)


def greeter(name: str) -> ToolResponse:
    """向某人打招呼。"""
    return ToolResponse(
        content=[TextBlock(type="text", text=f"你好，{name}！")],
    )


async def main() -> None:
    toolkit = Toolkit()
    toolkit.register_tool_function(greeter)

    # ── 注册限流中间件 ──
    call_times: list[float] = []
    rate_limit, window = 3, 60.0  # 每分钟最多 3 次

    async def rate_limit_middleware(kwargs, next_handler):
        """检查调用频率，超出上限则拒绝。"""
        now = time.time()
        while call_times and now - call_times[0] > window:
            call_times.pop(0)
        if len(call_times) >= rate_limit:
            print(f"  [限流] 已达上限，拒绝调用")
            yield ToolResponse(content=[TextBlock(
                type="text", text=f"限流: 每分钟最多 {rate_limit} 次")])
            return
        call_times.append(now)
        async for response in await next_handler(**kwargs):
            yield response

    toolkit.register_middleware(rate_limit_middleware)

    # ── 测试: 连续调用 5 次 ──
    for i in range(5):
        print(f"\n第 {i+1} 次调用:")
        async for chunk in await toolkit.call_tool_function(
            ToolUseBlock(type="tool_use", id=f"c{i}", name="greeter",
                         input={"name": f"用户{i}"}),
        ):
            print(f"  → {chunk.content[0]['text']}")


if __name__ == "__main__":
    asyncio.run(main())
