# 第 22 章：造一个新 Tool

**对应书籍：** 卷三 ch22
**对应源码：** `src/agentscope/tool/`

## 运行

```bash
python ch22-new-tool/custom_tool.py
```

## 学什么

- 如何定义一个符合 AgentScope 规范的工具函数
- register_tool_function 的完整参数
- JSON Schema 自动生成
- ToolResponse 的构造

## 源码跳转

- `src/agentscope/tool/_response.py` — ToolResponse 类型
- `src/agentscope/tool/_types.py` — ToolFunction 类型定义
- `src/agentscope/tool/_toolkit.py` — 注册和执行逻辑
