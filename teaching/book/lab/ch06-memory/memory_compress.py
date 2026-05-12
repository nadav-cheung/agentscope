# -*- coding: utf-8 -*-
"""Demonstrate memory compression with marks and summary."""

import asyncio
from typing import Any

# → src/agentscope/memory/_working_memory/_base.py:66 (get_memory with marks)
# → src/agentscope/memory/_working_memory/_in_memory_memory.py (compression logic)
from agentscope.memory._working_memory._in_memory_memory import InMemoryMemory
from agentscope.message import Msg


async def main() -> None:
    memory = InMemoryMemory()

    # Simulate a long conversation
    msgs: list[Msg] = []
    for i in range(5):
        msgs.append(Msg("user", f"Question {i}: tell me about topic {i}", "user"))
        msgs.append(
            Msg("assistant", f"Answer {i}: here is information about topic {i}",
                "assistant"),
        )

    # Mark first 2 rounds as core, rest as verbose
    for idx, msg in enumerate(msgs):
        mark: str | list[str] | None = (
            "core" if idx < 4 else "verbose"
        )
        await memory.add(msg, marks=mark)

    # Compress: set summary and re-mark verbose messages for exclusion
    await memory.update_compressed_summary(
        "Summary: topics 0-4 were discussed. Key points include ..."
    )

    # Retrieve only core messages + prepended summary
    result: list[Msg] = await memory.get_memory(
        mark="core",
        exclude_mark="verbose",
        prepend_summary=True,
    )
    for msg in result:
        role: str = msg.role
        content_preview: Any = (
            msg.content[:60] if isinstance(msg.content, str) else str(msg.content)
        )
        print(f"  [{role}] {content_preview}")

    print(f"\nTotal stored: {await memory.size()}, Retrieved: {len(result)}")


if __name__ == "__main__":
    asyncio.run(main())
