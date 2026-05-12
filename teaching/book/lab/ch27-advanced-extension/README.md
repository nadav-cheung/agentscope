# 第 27 章：高级扩展

**对应书籍：** 卷三 ch27
**对应源码：** `src/agentscope/tool/_toolkit.py`

## 运行

```bash
python ch27-advanced-extension/rate_limit_middleware.py
python ch27-advanced-extension/agent_skill.py
```

## 学什么

- 自定义中间件：如何给工具加限流、日志等横切逻辑
- Agent Skill：将提示词+工具打包为可复用单元
- create_tool_group：工具分组管理

## 源码跳转

- `src/agentscope/tool/_toolkit.py:57` — _apply_middlewares
- `src/agentscope/tool/_toolkit.py:1328` — register_agent_skill
- `src/agentscope/tool/_toolkit.py:187` — create_tool_group
- `src/agentscope/tool/_toolkit.py:1441` — register_middleware
