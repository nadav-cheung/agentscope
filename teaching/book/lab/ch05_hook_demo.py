"""第 5 章：Hook 系统演示 — pre_reply / post_reply 三层钩子

演示 AgentScope 的 hook 系统如何在不修改 Agent 源码的情况下
注入自定义逻辑。

Hook 系统三层结构：
  1. pre_reply  hook — 在 reply() 执行前触发，可修改请求参数
  2. reply()         — Agent 的核心推理循环
  3. post_reply hook — 在 reply() 执行后触发，可修改返回值
"""
import asyncio

import agentscope
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg, TextBlock
from agentscope.tool import Toolkit, ToolResponse

from config import get_model_and_formatter


def echo(text: str) -> ToolResponse:
    """工具：回显文本。"""
    return ToolResponse(content=[TextBlock(type="text", text=f"echo: {text}")])


async def main():
    agentscope.init(project="book-lab-ch05-hook")

    model, formatter = get_model_and_formatter()
    toolkit = Toolkit()
    toolkit.register_tool_function(echo)
    agent = ReActAgent(
        name="EchoBot",
        sys_prompt="你是 EchoBot。用户说任何话，你都先调用 echo 工具，然后回复。",
        model=model,
        formatter=formatter,
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    # ==================== 注册 pre_reply hook ====================
    # → src/agentscope/agent/_agent_base.py:533 (register_instance_hook)
    # → src/agentscope/agent/_agent_meta.py:106 (hook(self, kwargs) → dict|None)
    async def my_pre_reply(self_agent, kwargs: dict):
        print("[PRE-REPLY]  即将调用 reply()，当前参数:")
        print(f"              agent={self_agent.name}")
        msg = kwargs.get('args', [None])[0]
        print(f"              msg={msg.get_text_content() if msg else 'None'}")
        return None  # None = 不修改参数

    agent.register_instance_hook("pre_reply", "log_pre", my_pre_reply)

    # ==================== 注册 post_reply hook ====================
    # → src/agentscope/agent/_agent_meta.py:146 (hook(self, kwargs, output) → output|None)
    async def my_post_reply(self_agent, kwargs: dict, output):
        text = output.get_text_content() or "(tool call)"
        print(f"[POST-REPLY] reply() 已返回: {text[:60]}...")
        return None  # None = 不修改输出

    agent.register_instance_hook("post_reply", "log_post", my_post_reply)

    # ==================== 触发完整 hook 链 ====================
    print("=" * 60)
    result = await agent(Msg("user", "hello world", "user"))
    print("=" * 60)
    print(f"最终回复: {result.get_text_content()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
