# 第 25 章：造一个新 Agent 类型

**对应书籍：** 卷三 ch25
**对应源码：** `src/agentscope/agent/`

## 运行

```bash
python ch25-new-agent/plan_execute_agent.py
```

## 学什么

- AgentBase 的抽象接口：reply()、__call__()
- Plan-Execute vs ReAct 两种 Agent 模式
- 如何继承和扩展 Agent 行为
- 状态管理（state_dict）

## 源码跳转

- `src/agentscope/agent/_agent_base.py` — AgentBase 基类
- `src/agentscope/agent/_react_agent.py` — ReActAgent 参考
- `src/agentscope/agent/_react_agent_base.py` — ReActAgentBase
