# -*- coding: utf-8 -*-
"""Demonstrate InMemoryMemory CRUD operations."""

import asyncio

# → src/agentscope/memory/_working_memory/_base.py (MemoryBase abstract class)
# → src/agentscope/memory/_working_memory/_in_memory_memory.py (InMemoryMemory impl)
from agentscope.memory._working_memory._in_memory_memory import InMemoryMemory
from agentscope.message import Msg


async def main() -> None:
    memory = InMemoryMemory()

    msg_user = Msg("user", "What is the weather in Tokyo?", "user")
    msg_agent = Msg("assistant", "Let me check the weather for you.", "assistant")
    msg_tool = Msg("system", '{"city": "Tokyo", "temp": 22}', "system")

    await memory.add([msg_user, msg_agent], marks="conversation")
    await memory.add(msg_tool, marks=["tool_result", "conversation"])

    all_msgs = await memory.get_memory()
    print(f"Total messages: {len(all_msgs)}")

    conv_msgs = await memory.get_memory(mark="conversation")
    print(f"With mark='conversation': {len(conv_msgs)}")

    tool_msgs = await memory.get_memory(
        mark="conversation", exclude_mark="tool_result"
    )
    print(f"Excluding tool_result: {len(tool_msgs)}")

    await memory.delete([msg_tool.id])
    remaining = await memory.get_memory()
    print(f"After delete tool msg: {len(remaining)} (size={await memory.size()})")


if __name__ == "__main__":
    asyncio.run(main())
