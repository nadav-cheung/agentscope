"""第 2 章：什么是 Agent — 完整天气查询 Agent

这是全书的贯穿示例。切换 LLM_PROVIDER 环境变量即可在
DeepSeek / OpenAI / Anthropic 之间切换，Agent 代码完全不变。
这就是 AgentScope model/formatter 解耦设计的价值。
"""
import asyncio

import agentscope
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.tool import Toolkit

from config import get_model_and_formatter


def get_weather(city: str) -> str:
    """查询城市天气。→ src/agentscope/tool/_types.py (ToolFunction 类型)"""
    weather_db = {
        "北京": "晴，25°C，湿度30%",
        "上海": "多云，28°C，湿度65%",
        "深圳": "阵雨，30°C，湿度80%",
    }
    return weather_db.get(city, f"未找到 {city} 的天气数据")


async def main():
    agentscope.init(project="book-lab-ch02")

    # model + formatter 由 config.py 根据 .env 自动选择
    # → src/agentscope/model/       (模型适配层)
    # → src/agentscope/formatter/   (格式转换层)
    model, formatter = get_model_and_formatter()

    # 工具注册
    # → src/agentscope/tool/_toolkit.py:1284 (register_tool_function)
    toolkit = Toolkit()
    toolkit.register_tool_function(get_weather)

    # Agent 组装：六块积木搭起一个 Agent
    # → src/agentscope/agent/_react_agent.py  (ReActAgent 实现)
    # → src/agentscope/agent/_agent_base.py   (AgentBase 基类)
    # → src/agentscope/agent/_agent_meta.py   (_AgentMeta 元类)
    agent = ReActAgent(
        name="天气助手",
        sys_prompt="你是一个天气助手。用户询问天气时，调用 get_weather 工具。",
        model=model,
        formatter=formatter,
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    # await agent(msg) — 全书追踪的这一行
    # → src/agentscope/agent/_agent_base.py:197 (reply 方法)
    # → src/agentscope/agent/_react_agent.py:408 (_react_loop)
    msg = Msg("user", "北京今天天气怎么样？", "user")
    result = await agent(msg)

    print("=" * 50)
    print(f"Agent 最终回复: {result.get_text_content()}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
