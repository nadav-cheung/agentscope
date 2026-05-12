"""第 22 章：造一个新 Tool

演示：定义工具函数 → register_tool_function 注册 → 查看 LLM 看到的 JSON Schema
"""
# → src/agentscope/tool/_toolkit.py     (Toolkit 实现, register_tool_function)
# → src/agentscope/tool/_response.py    (ToolResponse 类型)
# → src/agentscope/tool/_types.py       (RegisteredToolFunction, ToolFunction 类型签名)

from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock


def get_stock_price(symbol: str) -> ToolResponse:
    """查询美股实时股价，返回最新成交价和涨跌幅。

    Args:
        symbol (`str`):
            股票代码，例如 AAPL, GOOGL, MSFT
    """
    # 模拟数据 — 真实场景替换为 API 调用
    mock_prices = {
        "AAPL": ("Apple Inc.", 187.32, "+1.24%"),
        "GOOGL": ("Alphabet Inc.", 142.65, "-0.53%"),
        "MSFT": ("Microsoft Corp.", 378.91, "+0.87%"),
    }
    info = mock_prices.get(
        symbol.upper(),
        (symbol, 0.0, "N/A"),
    )
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"{info[0]} ({symbol.upper()}): ${info[1]} ({info[2]})",
            ),
        ],
    )


def main() -> None:
    toolkit = Toolkit()

    # register_tool_function 关键参数:
    # - tool_func:       工具函数本身
    # - func_name:       自定义名称 (默认取函数 __name__)
    # - func_description: 自定义描述 (默认取 docstring)
    # - json_schema:     手动提供 JSON Schema (默认自动生成)
    toolkit.register_tool_function(
        get_stock_price,
        func_name="get_stock_price",
        func_description="查询指定美股的最新实时股价和涨跌幅信息",
    )

    # 查看 LLM 收到的 JSON Schema
    schemas = toolkit.get_json_schemas()
    import json
    print("LLM 看到的工具描述:")
    print(json.dumps(schemas, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
