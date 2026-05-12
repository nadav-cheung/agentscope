"""第 24 章：造一个新 Memory Backend

演示基于 SQLite 的持久化 Memory 实现,展示 MemoryBase 的 5 个抽象方法。
"""
import sqlite3
from typing import Any

# → src/agentscope/memory/_working_memory/_base.py            (MemoryBase 抽象类)
# → src/agentscope/memory/_working_memory/_in_memory_memory.py (参考实现)
# → src/agentscope/module/_state_module.py                    (StateModule, state_dict)

from agentscope.memory._working_memory._base import MemoryBase
from agentscope.message import Msg


class SQLiteMemory(MemoryBase):
    """基于 SQLite 的持久化 Memory 实现。

    与 InMemoryMemory 的核心区别：数据写入磁盘，重启不丢失。
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        super().__init__()
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "  msg_id TEXT PRIMARY KEY,"
            "  msg_json TEXT NOT NULL,"
            "  marks TEXT NOT NULL DEFAULT ''"
            ")"
        )
        self._conn.commit()

    # ---- 5 个抽象方法 ----

    async def add(
        self,
        memories: Msg | list[Msg] | None,
        marks: str | list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        if memories is None:
            return
        if isinstance(memories, Msg):
            memories = [memories]
        if isinstance(marks, str):
            marks = [marks]
        marks_str = ",".join(marks or [])
        for msg in memories:
            self._conn.execute(
                "INSERT OR REPLACE INTO messages VALUES (?, ?, ?)",
                (msg.id, msg.to_dict_str(), marks_str),
            )
        self._conn.commit()

    async def get_memory(
        self,
        mark: str | None = None,
        **kwargs: Any,
    ) -> list[Msg]:
        if mark:
            rows = self._conn.execute(
                "SELECT msg_json FROM messages WHERE ',' || marks || ',' LIKE ?",
                (f"%,{mark},%",),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT msg_json FROM messages").fetchall()
        return [Msg.from_dict_str(row[0]) for row in rows]

    async def delete(self, msg_ids: list[str], **kwargs: Any) -> int:
        placeholders = ",".join("?" * len(msg_ids))
        cur = self._conn.execute(
            f"DELETE FROM messages WHERE msg_id IN ({placeholders})",
            msg_ids,
        )
        self._conn.commit()
        return cur.rowcount

    async def clear(self) -> None:
        self._conn.execute("DELETE FROM messages")
        self._conn.commit()

    async def size(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    # ---- StateModule 序列化协议 ----

    def state_dict(self) -> dict[str, Any]:
        """导出为字典 — 持久化到 checkpoint。"""
        return {"db_path": self.db_path}

    def from_state_dict(self, state: dict[str, Any]) -> None:
        """从字典恢复 — 如从 checkpoint 恢复。"""
        self.db_path = state.get("db_path", self.db_path)


async def main() -> None:
    print("第 24 章：SQLite Memory Backend\n")

    mem = SQLiteMemory()  # :memory: 模式，演示用
    await mem.add(Msg("user", "Hello, world!", "user"), marks="greeting")
    await mem.add(Msg("assistant", "Hi there!", "assistant"), marks="greeting")

    msgs = await mem.get_memory(mark="greeting")
    print(f"greeting 标签下的消息: {len(msgs)}")
    for m in msgs:
        print(f"  [{m.role}] {m.get_text_content()}")

    print(f"\n总消息数: {await mem.size()}")
    print(f"状态字典: {mem.state_dict()}")

    # 对比 InMemoryMemory: 进程重启后数据消失
    # SQLiteMemory: 数据持久化到磁盘


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
