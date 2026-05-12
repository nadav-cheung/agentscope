# 第 4 章：消息诞生

**对应书籍：** 卷一 ch04
**对应源码：** `src/agentscope/message/`

## 运行

```bash
python ch04-message/msg_create.py
python ch04-message/msg_serialize.py
```

## 学什么

- Msg 的内部结构：name、content、role
- 七种 ContentBlock：Text、Image、ToolUse、ToolResult、Audio、Thinking、Citation
- 消息的序列化与反序列化（to_dict / from_dict）

## 源码跳转

读完此文件后，打开：
- `src/agentscope/message/_message_base.py` — Msg 类完整实现
- `src/agentscope/message/_message_block.py` — 所有 ContentBlock 类型定义
