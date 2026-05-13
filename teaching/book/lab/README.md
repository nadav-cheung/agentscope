# AgentScope 源码之旅 — 配套代码

这是《AgentScope 源码之旅》书籍的配套可运行代码，位于 `teaching/book/lab/`。

你在 clone 本书仓库时已经拿到了所有代码。

## 快速开始

```bash
cd teaching/book/lab
python -m venv .venv && source .venv/bin/activate
pip install agentscope python-dotenv
cp .env.example .env
# 编辑 .env，填入任意一个 provider 的 API key
```

## 三种运行方式

| 方式 | 命令 | 需要 API key |
|------|------|-------------|
| DeepSeek（推荐） | `python ch02_weather_agent.py` | DeepSeek 免费额度 |
| OpenAI | `LLM_PROVIDER=openai python ...` | OpenAI key |
| Anthropic | `LLM_PROVIDER=anthropic python ...` | Anthropic key |
| 离线 Mock | `MOCK=1 python ...` | **不需要** |

## 目录导航

| 章节文件 | 对应源码 | 学什么 |
|---------|---------|--------|
| ch01_hello_llm | `src/agentscope/model/` | 第一行代码，跑通 LLM 调用 |
| ch02_weather_agent | `src/agentscope/agent/` | 完整天气 Agent，理解 ReAct |
| ch02_pure_python_loop | `src/agentscope/agent/` | 纯 Python 循环 vs Agent 框架对比 |
| ch04_msg_create / ch04_msg_serialize | `src/agentscope/message/` | Msg 的七种 ContentBlock |
| ch05_agent_call_flow / ch05_hook_demo | `src/agentscope/agent/` | Agent 收信 → reply 调用链 |
| ch06_memory_store / ch06_memory_compress | `src/agentscope/memory/` | InMemoryMemory 增删查 |
| ch08_openai_format / ch08_anthropic_format | `src/agentscope/formatter/` | OpenAI vs Anthropic 格式转换 |
| ch09_sync_vs_stream / ch09_structured_output | `src/agentscope/model/` | 同步/流式调用，结构化输出 |
| ch10_register_tool / ch10_middleware_demo | `src/agentscope/tool/` | 工具注册 + 中间件洋葱模型 |
| ch11_react_loop | `src/agentscope/agent/` | ReAct 完整循环，逐步日志 |
| ch22-ch28 | 各模块 | 造新 Tool / Model / Memory / Agent |

## 源码指针

代码注释中的 `# → src/agentscope/...` 指向仓库中的实际源码位置。读完 companion 代码后，顺着指针跳转到真正的实现。

## 验证源码指针

```bash
python verify_companion.py
# 输出所有指针是否仍然有效
```
