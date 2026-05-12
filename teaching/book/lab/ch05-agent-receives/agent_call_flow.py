"""第 5 章：Agent 收信 — 追踪 await agent(msg) 完整调用链

追踪一行代码背后的完整调用链路，理解 AgentScope 的请求-响应流水线。
使用 MOCK=1 离线运行，无需 API key。
"""
import asyncio

import agentscope
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.tool import Toolkit

from config import get_model_and_formatter


def echo(text: str) -> str:
    """最简单的工具：回显文本。"""
    return f"echo: {text}"


async def main():
    # ========================= 初始化 =========================
    # → src/agentscope/_init.py (初始化 session、tracing 等基础设施)
    agentscope.init(project="book-lab-ch05")

    model, formatter = get_model_and_formatter()

    # ========================= 组装 Agent =========================
    # ReActAgent 的元类是 _AgentMeta，它在类创建时用 _wrap_with_hooks
    # 自动包装 reply / observe / print 方法，注入 hook 触发逻辑。
    # → src/agentscope/agent/_agent_meta.py:55  (_wrap_with_hooks)
    # → src/agentscope/agent/_agent_meta.py:159 (_AgentMeta 元类)

    toolkit = Toolkit()
    toolkit.register_tool_function(echo)
    # → src/agentscope/tool/_toolkit.py (register_tool_function)

    agent = ReActAgent(
        name="EchoBot",
        sys_prompt="You are an echo bot. When the user says something, "
        "call the echo tool with their message, then reply.",
        model=model,
        formatter=formatter,
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    # ========================= 核心追踪 =========================
    # 这一行是全书追踪的起点。背后发生了什么？
    #
    #   await agent(msg)
    #     │
    #     ├─ 1. _AgentMeta 保证了 agent 的 reply 已被 _wrap_with_hooks 包装
    #     │     → src/agentscope/agent/_agent_meta.py:55
    #     │
    #     ├─ 2. __call__ 生成 reply_id，启动 asyncio task，调用 reply
    #     │     → src/agentscope/agent/_agent_base.py:448 (__call__ 方法)
    #     │
    #     ├─ 3. _wrap_with_hooks 执行 pre_reply hooks（如果有）
    #     │       → 修改或记录请求参数
    #     │     → src/agentscope/agent/_agent_meta.py:99 (pre-hooks 循环)
    #     │
    #     ├─ 4. reply()  →  ReActAgent._react_loop()
    #     │     → src/agentscope/agent/_agent_base.py:197 (reply 抽象方法)
    #     │     → src/agentscope/agent/_react_agent.py (ReAct 循环实现)
    #     │
    #     ├─ 5. _wrap_with_hooks 执行 post_reply hooks（如果有）
    #     │       → 修改、记录或流式转发回复消息
    #     │     → src/agentscope/agent/_agent_meta.py:139 (post-hooks 循环)
    #     │
    #     └─ 6. __call__ 广播回复到 subscribers（pipeline 协作模式）
    #           → src/agentscope/agent/_agent_base.py:464 (_broadcast_to_subscribers)

    msg = Msg("user", "hello!", "user")
    print(">>> 发出消息:", msg.get_text_content())

    result = await agent(msg)
    #         ^^^^^^^^^^^^^^^  ← 全书追踪的这一行

    print("<<< Agent 回复:", result.get_text_content())


if __name__ == "__main__":
    asyncio.run(main())
