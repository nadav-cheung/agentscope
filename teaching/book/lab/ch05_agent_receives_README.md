# 第 5 章：Agent 收信

**对应书籍：** 卷一 ch05
**对应源码：** `src/agentscope/agent/_agent_base.py`, `src/agentscope/agent/_agent_meta.py`

## 运行

```bash
# 离线模式（无需 API key）
MOCK=1 python ch05-agent-receives/agent_call_flow.py
MOCK=1 python ch05-agent-receives/hook_demo.py
```

## 学什么

- `await agent(msg)` 的完整调用链：__call__ → reply → hooks
- _AgentMeta 元类如何自动包装方法
- Hook 系统的三层结构（pre_reply / post_reply / 广播）

## 源码跳转

- `src/agentscope/agent/_agent_base.py:448` — __call__ 方法
- `src/agentscope/agent/_agent_base.py:197` — reply 方法
- `src/agentscope/agent/_agent_meta.py` — _AgentMeta 元类 + _wrap_with_hooks
