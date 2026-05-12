"""Provider configuration for AgentScope book companion.

Usage — copy-paste into any chapter script:
    from config import get_model_and_formatter
    model, formatter = get_model_and_formatter()

Provider selection via environment (edit .env):
    LLM_PROVIDER=deepseek    # recommended: free credits, dual format
    LLM_PROVIDER=openai      # standard OpenAI
    LLM_PROVIDER=anthropic   # Anthropic or DeepSeek Anthropic endpoint

Offline mode:
    MOCK=1 python ch02-hello-agent/weather_agent.py
"""
import os

from dotenv import load_dotenv

load_dotenv()


def get_model_and_formatter():
    """Return (model, formatter) based on LLM_PROVIDER and MOCK env vars."""

    # ── Mock mode: no real API call ─────────────────────────
    if os.getenv("MOCK") == "1":
        from agentscope.model import OpenAIChatModel
        from agentscope.formatter import OpenAIChatFormatter

        model = OpenAIChatModel(
            model_name="mock-model",
            api_key="mock",
            client_kwargs={"base_url": "http://127.0.0.1:9999/v1"},
        )
        formatter = OpenAIChatFormatter()
        return model, formatter

    # ── Real providers ──────────────────────────────────────
    provider = os.getenv("LLM_PROVIDER", "deepseek").lower()

    if provider == "deepseek":
        # → src/agentscope/model/_openai_model.py
        # → src/agentscope/formatter/_openai_formatter.py
        from agentscope.model import OpenAIChatModel
        from agentscope.formatter import OpenAIChatFormatter

        model = OpenAIChatModel(
            model_name="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            client_kwargs={"base_url": "https://api.deepseek.com/v1"},
        )
        formatter = OpenAIChatFormatter()

    elif provider == "openai":
        from agentscope.model import OpenAIChatModel
        from agentscope.formatter import OpenAIChatFormatter

        model = OpenAIChatModel(
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        formatter = OpenAIChatFormatter()

    elif provider == "anthropic":
        # DeepSeek Anthropic endpoint also works via ANTHROPIC_BASE_URL
        from agentscope.model import OpenAIChatModel
        from agentscope.formatter import AnthropicChatFormatter

        model = OpenAIChatModel(
            model_name=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            client_kwargs={
                "base_url": os.getenv(
                    "ANTHROPIC_BASE_URL",
                    "https://api.anthropic.com/v1",
                ),
            },
        )
        # → src/agentscope/formatter/_anthropic_formatter.py
        formatter = AnthropicChatFormatter()

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER={provider!r}. "
            f"Set to deepseek, openai, or anthropic in .env"
        )

    return model, formatter
