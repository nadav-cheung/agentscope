# 第 6 章：工作记忆

**对应书籍：** 卷一 ch06
**对应源码：** `src/agentscope/memory/_working_memory/`

## 运行

```bash
python ch06-memory/memory_store.py
python ch06-memory/memory_compress.py
```

## 学什么

- MemoryBase 的 5 个抽象方法
- InMemoryMemory 的列表结构
- 记忆压缩（summary）和标记过滤（marks）

## 源码跳转

- `src/agentscope/memory/_working_memory/_base.py` — MemoryBase 抽象基类
- `src/agentscope/memory/_working_memory/_in_memory_memory.py` — 内存实现
