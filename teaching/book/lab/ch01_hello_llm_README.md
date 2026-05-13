# 第 1 章：什么是大模型（LLM）

**对应书籍：** 卷零 ch01
**对应源码：** `src/agentscope/model/`

## 运行

```bash
# 需要 API key
python ch01-hello-llm/hello_llm.py

# 或用 config.py 多 provider 版本（推荐）
python ch02-hello-agent/weather_agent.py
```

## 学什么

- LLM API 调用的基本结构
- AgentScope 的 `OpenAIChatModel` 如何使用
- 消息格式（system / user / assistant）

## 源码跳转

读完此文件后，打开：
- `src/agentscope/model/_model_base.py` — ChatModelBase 基类
- `src/agentscope/model/_openai_model.py` — OpenAI 模型适配
