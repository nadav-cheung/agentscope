# 第 8 章：格式转换

**对应书籍：** 卷一 ch08
**对应源码：** `src/agentscope/formatter/`

## 运行

```bash
python ch08-formatter/openai_format.py
python ch08-formatter/anthropic_format.py
```

## 学什么

- Msg → API 消息格式的转换过程
- OpenAI 和 Anthropic 两种格式的结构差异
- FormatterBase → TruncatedFormatterBase → OpenAIChatFormatter 三层继承

## 源码跳转

- `src/agentscope/formatter/_formatter_base.py` — FormatterBase 基类
- `src/agentscope/formatter/_truncated_formatter_base.py` — Token 截断逻辑
- `src/agentscope/formatter/_openai_formatter.py` — OpenAI 格式化
- `src/agentscope/formatter/_anthropic_formatter.py` — Anthropic 格式化
