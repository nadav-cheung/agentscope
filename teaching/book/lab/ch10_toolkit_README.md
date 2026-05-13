# 第 10 章：执行工具

**对应书籍：** 卷一 ch10
**对应源码：** `src/agentscope/tool/`

## 运行

```bash
python ch10-toolkit/register_tool.py
python ch10-toolkit/middleware_demo.py
```

## 学什么

- Toolkit.register_tool_function 的注册流程
- 工具执行的完整路径：ToolUseBlock → 函数调用 → ToolResponse
- 中间件的洋葱模型

## 源码跳转

- `src/agentscope/tool/_toolkit.py` — Toolkit 完整实现
- `src/agentscope/tool/_response.py` — ToolResponse 类型
- `src/agentscope/tool/_types.py` — ToolFunction 类型定义
