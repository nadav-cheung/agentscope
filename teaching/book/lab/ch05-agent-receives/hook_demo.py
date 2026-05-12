"""第 5 章：Hook 系统演示 — pre_reply / post_reply 三层钩子

演示 AgentScope 的 hook 系统如何在不修改 Agent 源码的情况下
注入自定义逻辑。使用 MOCK=1 离线运行，无需 API key。

Hook 系统三层结构：
  1. pre_reply  hook — 在 reply() 执行前触发，可修改请求参数
  2. reply()         — Agent 的核心推理循环
  3. post_reply hook — 在 reply() 执行后触发，可修改返回值
"""
import asyncio

import agentscope
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.tool import Toolkit

from config import get_model_and_formatter


def echo(text: str) -> str:
    """工具：回显文本。"""
    return f"echo: {text}"


async def main():
    agentscope.init(project="book-lab-ch05-hooks")

    model, formatter = get_model_and_formatter()

    toolkit = Toolkit()
    toolkit.register_tool_function(echo)

    agent = ReActAgent(
        name="HookBot",
        sys_prompt="You are a bot. Call echo tool for every user message.",
        model=model,
        formatter=formatter,
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    # ==================== 注册 pre_reply hook ====================
    # → src/agentscope/agent/_agent_base.py:533 (register_instance_hook)
    # → src/agentscope/agent/_agent_meta.py:99   (pre-hooks 执行循环)
    # pre_reply hook 接收 kwargs dict，可返回修改后的 kwargs

    async def my_pre_reply(kwargs: dict) -> dict:
        print("[PRE-REPLY]  即将调用 reply()，当前参数:")
        print(f"              agent={kwargs.get('self').name}")
        print(f"              args={[m.get_text_content() for m in kwargs.get('args', [])]}")
        return kwargs  # 原样返回 = 不修改参数

    agent.register_instance_hook("pre_reply", "log_pre", my_pre_reply)

    # ==================== 注册 post_reply hook ====================
    # → src/agentscope/agent/_agent_meta.py:139  (post-hooks 执行循环)
    # post_reply hook 接收 kwargs + 原始输出，可返回修改后的输出

    async def my_post_reply(kwargs: dict, output: Msg) -> Msg:
        print(f"[POST-REPLY] reply() 已返回: {output.get_text_content()[:60]}...")
        return output  # 原样返回 = 不修改输出

    agent.register_instance_hook("post_reply", "log_post", my_post_reply)

    # ==================== 触发完整 hook 链 ====================
    print("=" * 60)
    print("发送消息: 'hello world'")
    print("=" * 60)

    result = await agent(Msg("user", "hello world", "user"))

    print("=" * 60)
    print(f"最终返回: {result.get_text_content()}")
    print("=" * 60)
    print("\nHook 链执行顺序: pre_reply → reply → post_reply")


if __name__ == "__main__":
    asyncio.run(main())
