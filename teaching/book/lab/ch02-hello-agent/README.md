# 第 2 章：什么是 Agent

**对应书籍：** 卷零 ch02
**对应源码：** `src/agentscope/agent/`, `src/agentscope/tool/`

## 运行

```bash
# 需要 API key（三选一）
LLM_PROVIDER=deepseek python ch02-hello-agent/weather_agent.py
LLM_PROVIDER=openai python ch02-hello-agent/weather_agent.py
LLM_PROVIDER=anthropic python ch02-hello-agent/weather_agent.py

# 离线模式
MOCK=1 python ch02-hello-agent/weather_agent.py

# 纯 Python 模拟（完全不需要 AgentScope）
python ch02-hello-agent/pure_python_loop.py
```

## 学什么

- ReAct Agent 的六块积木：model、formatter、toolkit、memory、sys_prompt、name
- `await agent(msg)` 这行代码背后发生了什么
- 用纯 Python 理解 ReAct 循环（Think → Act → Think → Answer）

## 源码跳转

读完此文件后，打开：
- `src/agentscope/agent/_react_agent.py` — ReActAgent 完整实现
- `src/agentscope/agent/_agent_base.py` — AgentBase 基类
- `src/agentscope/agent/_agent_meta.py` — _AgentMeta 元类
- `src/agentscope/tool/_toolkit.py` — Toolkit 注册与执行
