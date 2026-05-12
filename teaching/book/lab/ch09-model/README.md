# 第 9 章：调用模型

**对应书籍：** 卷一 ch09
**对应源码：** `src/agentscope/model/`

## 运行

```bash
python ch09-model/sync_vs_stream.py
python ch09-model/structured_output.py
```

## 学什么

- 同步调用 vs 流式调用的区别
- AsyncGenerator 在流式解析中的作用
- 结构化输出：如何让 LLM 返回 JSON

## 源码跳转

- `src/agentscope/model/_model_base.py` — ChatModelBase 基类
- `src/agentscope/model/_openai_model.py` — OpenAI 模型适配（含流式+结构化输出）
