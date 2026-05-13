# -*- coding: utf-8 -*-
"""Unit tests for the book companion config module."""
import os
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import patch


class TestGetModelAndFormatter(IsolatedAsyncioTestCase):
    """Test cases for get_model_and_formatter()."""

    def test_mock_mode_returns_openai_model_and_formatter(self) -> None:
        """MOCK=1 should return OpenAIChatModel + OpenAIChatFormatter."""
        with patch.dict(os.environ, {"MOCK": "1"}, clear=True):
            from config import get_model_and_formatter

            from agentscope.formatter import OpenAIChatFormatter
            from agentscope.model import OpenAIChatModel

            model, formatter = get_model_and_formatter()
            self.assertIsInstance(model, OpenAIChatModel)
            self.assertIsInstance(formatter, OpenAIChatFormatter)
            self.assertEqual(model.model_name, "mock-model")

    def test_deepseek_provider(self) -> None:
        """LLM_PROVIDER=deepseek returns OpenAIChatModel with deepseek config."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "sk-test"},
            clear=True,
        ):
            from config import get_model_and_formatter

            from agentscope.formatter import OpenAIChatFormatter
            from agentscope.model import OpenAIChatModel

            model, formatter = get_model_and_formatter()
            self.assertIsInstance(model, OpenAIChatModel)
            self.assertIsInstance(formatter, OpenAIChatFormatter)
            self.assertEqual(model.model_name, "deepseek-chat")

    def test_openai_provider(self) -> None:
        """LLM_PROVIDER=openai returns OpenAIChatModel with openai config."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"},
            clear=True,
        ):
            from config import get_model_and_formatter

            from agentscope.formatter import OpenAIChatFormatter
            from agentscope.model import OpenAIChatModel

            model, formatter = get_model_and_formatter()
            self.assertIsInstance(model, OpenAIChatModel)
            self.assertIsInstance(formatter, OpenAIChatFormatter)
            self.assertIn("gpt", model.model_name)

    def test_anthropic_provider(self) -> None:
        """LLM_PROVIDER=anthropic returns AnthropicChatModel."""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-ant-test",
            },
            clear=True,
        ):
            from config import get_model_and_formatter

            from agentscope.formatter import AnthropicChatFormatter
            from agentscope.model import AnthropicChatModel

            model, formatter = get_model_and_formatter()
            self.assertIsInstance(model, AnthropicChatModel)
            self.assertIsInstance(formatter, AnthropicChatFormatter)

    def test_anthropic_auth_token_fallback(self) -> None:
        """ANTHROPIC_AUTH_TOKEN is used when ANTHROPIC_API_KEY is unset."""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_AUTH_TOKEN": "sk-ant-from-token",
                "ANTHROPIC_API_KEY": "",
            },
            clear=True,
        ):
            from config import get_model_and_formatter

            from agentscope.model import AnthropicChatModel

            model, _formatter = get_model_and_formatter()
            self.assertIsInstance(model, AnthropicChatModel)

    def test_default_provider_is_deepseek(self) -> None:
        """When LLM_PROVIDER is unset, deepseek is the default."""
        with patch.dict(
            os.environ,
            {"DEEPSEEK_API_KEY": "sk-test"},
            clear=True,
        ):
            from config import get_model_and_formatter

            from agentscope.model import OpenAIChatModel

            model, _formatter = get_model_and_formatter()
            self.assertEqual(model.model_name, "deepseek-chat")

    def test_unknown_provider_raises_value_error(self) -> None:
        """Unknown LLM_PROVIDER raises ValueError."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "unknown-provider"},
            clear=True,
        ):
            from config import get_model_and_formatter

            with self.assertRaises(ValueError):
                get_model_and_formatter()

    def test_anthropic_without_api_key_raises(self) -> None:
        """Anthropic provider without any API key raises ValueError."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "anthropic"},
            clear=True,
        ):
            from config import get_model_and_formatter

            with self.assertRaises(ValueError):
                get_model_and_formatter()


if __name__ == "__main__":
    import unittest

    unittest.main()
