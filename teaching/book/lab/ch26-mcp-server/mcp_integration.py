"""第 26 章：集成 MCP Server — 将外部工具服务器接入 AgentScope

MCP 架构: 外部 MCP Server → MCP Client → Toolkit.register_mcp_client()
→ Agent 即可透明使用 MCP 工具（无需关心工具来源）。
"""
import asyncio

from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock

# → src/agentscope/mcp/                        (MCP 客户端)
# → src/agentscope/mcp/_http_stateless_client.py (HTTP MCP 客户端)
# → src/agentscope/mcp/_mcp_function.py         (MCPToolFunction)
# → src/agentscope/tool/_toolkit.py:1035        (register_mcp_client)


def mock_mcp_tool(location: str) -> ToolResponse:
    """查询天气（模拟 MCP 远程工具）。"""
    db = {"北京": "晴 22°C", "上海": "多云 26°C", "深圳": "阵雨 30°C"}
    return ToolResponse(
        content=[TextBlock(type="text", text=db.get(location, "未知"))],
    )


async def main() -> None:
    """演示 MCP 集成的完整流程。"""
    print("=" * 55)
    print("MCP Server 集成架构演示")
    print("=" * 55)

    # 1. MCP Server 提供工具（真实场景: 独立进程 via stdio/sse/http）
    print("\n[1] MCP Server 提供远程工具")

    # 2. 注册到 Toolkit
    # 真实流程: tk.register_mcp_client(HttpStatelessClient(...))
    #   → list_tools() → 创建 MCPToolFunction → 注册到 tools 字典
    toolkit = Toolkit()
    toolkit.register_tool_function(mock_mcp_tool)
    print(f"[2] 已注册: {list(toolkit.tools.keys())}")

    # 3. Agent 透明调用
    # Agent._reasoning → LLM 返回 tool_use → call_tool_function
    # → MCPToolFunction.__call__ → 开启 session → call_tool → 关闭
    result = mock_mcp_tool("北京")
    print(f"[3] 调用 get_weather('北京'): {result.content[0]['text']}")

    print("\n集成要点: Agent 无需感知工具来自本地还是远程 MCP Server")


if __name__ == "__main__":
    asyncio.run(main())
