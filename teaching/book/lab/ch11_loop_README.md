# 第 11 章：循环与返回

**对应书籍：** 卷一 ch11
**对应源码：** `src/agentscope/agent/_react_agent.py`

## 运行

```bash
python ch11-loop/react_loop.py
```

## 学什么

- ReAct 循环的 5 个阶段：准备 → 推理 → 行动 → 观察 → 判断
- 并行工具执行（asyncio.gather）
- 记忆压缩滑动窗口
- 循环终止条件

## 源码跳转

- `src/agentscope/agent/_react_agent.py:408` — _react_loop 主循环
- `src/agentscope/agent/_react_agent.py:1015` — _acting 工具执行
