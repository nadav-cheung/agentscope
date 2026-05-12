# 第 26 章：集成 MCP Server

**对应书籍：** 卷三 ch26
**对应源码：** `src/agentscope/mcp/`

## 运行

```bash
python ch26-mcp-server/mcp_integration.py
```

## 学什么

- MCP (Model Context Protocol) 是什么
- 如何将外部 MCP Server 的工具注册到 AgentScope
- AgentScope 的 MCP 客户端架构

## 源码跳转

- `src/agentscope/mcp/` — MCP 客户端实现
- `src/agentscope/tool/_toolkit.py` — 工具注册（register_mcp_client）
- `src/agentscope/mcp/_http_stateless_client.py` — HTTP 传输
- `src/agentscope/mcp/_stdio_stateful_client.py` — stdio 传输
