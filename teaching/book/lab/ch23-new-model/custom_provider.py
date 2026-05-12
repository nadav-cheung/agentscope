"""第 23 章：造一个新 Model Provider

演示 ChatModelBase 抽象接口 → OpenAIChatModel 参考实现 → 自定义 Provider 模式
不实际发起 API 调用，专注于架构层次和扩展点。
"""
# → src/agentscope/model/_model_base.py     (ChatModelBase 抽象接口)
# → src/agentscope/model/_openai_model.py   (OpenAI 参考实现)
# → src/agentscope/formatter/_formatter_base.py (Formatter 配对关系)

from agentscope.model import OpenAIChatModel


# ============================================================
# 步骤 1：理解 ChatModelBase 提供的抽象接口
# ============================================================
# ChatModelBase 定义了所有模型的合约:
#
#   class ChatModelBase:
#       model_name: str     # 模型名称标识
#       stream: bool        # 是否流式输出
#
#       async def __call__(self, *args, **kwargs):
#           '''抽象方法 — 子类必须实现模型调用逻辑'''
#
# 核心约束: __call__ 必须返回 ChatResponse | AsyncGenerator[ChatResponse]


# ============================================================
# 步骤 2：OpenAIChatModel — 最常用的参考实现
# ============================================================
# OpenAIChatModel(ChatModelBase) 额外提供:
#   - __init__: api_key / organization / client_kwargs / generate_kwargs
#   - __call__: 调用 OpenAI HTTP API，支持 streaming / tool_use / structured output
#   - 内部使用 openai.AsyncOpenAI 客户端
#
# 分离关注点: Model 只管"怎么发请求"，Formatter 只管"怎么格式化消息"


# ============================================================
# 步骤 3：演示自定义 Provider 的扩展模式
# ============================================================
class CustomProviderModel(OpenAIChatModel):
    """接入自定义 OpenAI 兼容 API (如 vLLM / LiteLLM / 本地模型)。

    只需覆盖 __init__ 设置默认 base_url 和 model_name，
    其余 HTTP 调用、流式处理、工具调用全部继承自 OpenAIChatModel。
    """

    def __init__(
        self,
        model_name: str = "local-model",
        api_key: str | None = None,
        stream: bool = True,
        base_url: str = "http://localhost:8000/v1",
    ):
        """初始化自定义 provider。

        Args:
            model_name: 本地部署的模型名称
            api_key: API key (本地模型通常不需要)
            stream: 是否流式输出
            base_url: 兼容 OpenAI 协议的 API 地址
        """
        super().__init__(
            model_name=model_name,
            api_key=api_key or "not-needed",
            stream=stream,
            client_kwargs={"base_url": base_url},
        )

    # pylint: disable=missing-function-docstring
    def _check_api_key(self) -> bool:
        """演示：可以添加 provider 特有的校验逻辑。"""
        return True  # 本地模型不需要 key


def main() -> None:
    print("=" * 50)
    print("第 23 章：造一个新 Model Provider")
    print("=" * 50)

    # 实例化自定义 provider
    model = CustomProviderModel(
        model_name="qwen2.5-7b-instruct",
        base_url="http://localhost:8000/v1",
    )
    print(f"Model name : {model.model_name}")
    print(f"Stream     : {model.stream}")
    print(f"API key ok : {model._check_api_key()}")

    print("\n扩展点总结:")
    print("  1. 子类 OpenAIChatModel → 改 base_url 接入 OpenAI 兼容 API")
    print("  2. 子类 ChatModelBase   → 完全自定义协议 (如 gRPC)")
    print("  3. 配对的 Formatter     → 负责消息格式转换")


if __name__ == "__main__":
    main()
