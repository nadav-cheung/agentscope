"""第 11 章：ReAct 循环 — 准备 → 推理 → 行动 → 观察 → 判断"""
import asyncio

import agentscope
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg, TextBlock
from agentscope.tool import Toolkit, ToolResponse

from config import get_model_and_formatter

# → src/agentscope/agent/_react_agent.py:408 (_react_loop 主循环)
# → src/agentscope/agent/_react_agent.py:1015 (_acting 工具执行)
# → src/agentscope/agent/_react_agent.py:318 (knowledge base 设置)


def get_weather(city: str) -> ToolResponse:
    """查询城市天气。"""
    db = {"北京": "晴，25°C，湿度30%", "上海": "多云，28°C", "深圳": "阵雨，30°C"}
    return ToolResponse(content=[TextBlock(type="text", text=db.get(city, "未知"))])


async def main() -> None:
    agentscope.init(project="book-lab-ch11")

    # ═══════ 阶段 1: 准备 — 组装 Agent ═══════
    print("=" * 60)
    print("阶段 1: 准备 — 组装 Agent")
    print("=" * 60)
    model, formatter = get_model_and_formatter()
    toolkit = Toolkit()
    toolkit.register_tool_function(get_weather)

    agent = ReActAgent(
        name="天气助手",
        sys_prompt="你是一个天气助手。用户询问天气时调用 get_weather 工具。",
        model=model,
        formatter=formatter,
        toolkit=toolkit,
        memory=InMemoryMemory(),
        max_iters=5,
    )
    print(f"Agent 组装完成，最大推理轮数: {agent.max_iters}")

    # ═══════ 阶段 2-5: ReAct 循环 ═══════
    # 内部步骤: _reasoning → _acting → 写入 memory → 判断是否退出
    #   第1轮: 模型返回 tool_use("get_weather", city="北京")
    #          执行 get_weather("北京") → "晴，25°C"
    #          工具结果写入 memory → 继续下一轮
    #   第2轮: 模型根据 "晴，25°C" 生成文本回复
    #          本轮无 tool_use → 退出循环
    # 退出条件: 纯文本 / max_iters 上限 / structured_model / 用户中断
    print()
    print("=" * 60)
    print("阶段 2-5: ReAct 循环（内部自动执行）")
    print("=" * 60)

    msg = Msg("user", "北京今天天气怎么样？", "user")
    print(f"用户输入: {msg.get_text_content()}\n")

    result = await agent(msg)

    print()
    print("=" * 60)
    print(f"最终回复: {result.get_text_content()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
