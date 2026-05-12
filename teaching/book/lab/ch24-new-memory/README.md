# 第 24 章：造一个新 Memory Backend

**对应书籍：** 卷三 ch24
**对应源码：** `src/agentscope/memory/`

## 运行

```bash
python ch24-new-memory/sqlite_memory.py
```

## 学什么

- MemoryBase 的 5 个抽象方法如何实现
- SQLite 作为持久化后端
- state_dict / from_state_dict 序列化协议
- 与 InMemoryMemory 的对比

## 源码跳转

- `src/agentscope/memory/_working_memory/_base.py` — MemoryBase 抽象基类
- `src/agentscope/memory/_working_memory/_in_memory_memory.py` — 参考实现
- `src/agentscope/module/_state_module.py` — StateModule 基类
