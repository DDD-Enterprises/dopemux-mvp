"""Tests for XAI provider implementation."""

import os
from unittest.mock import MagicMock, patch

import pytest

from providers.shared import ProviderType
from providers.xai import XAIModelProvider


class TestXAIProvider:
    def setup_method(self):
        import utils.model_restrictions

        utils.model_restrictions._restriction_service = None

    def teardown_method(self):
        import utils.model_restrictions

        utils.model_restrictions._restriction_service = None

    @patch.dict(os.environ, {"XAI_API_KEY": "test-key"})
    def test_initialization(self):
        provider = XAIModelProvider("test-key")

        assert provider.api_key == "test-key"
        assert provider.get_provider_type() == ProviderType.XAI
        assert provider.base_url == "https://api.x.ai/v1"

    def test_initialization_with_custom_url(self):
        provider = XAIModelProvider("test-key", base_url="https://custom.x.ai/v1")

        assert provider.base_url == "https://custom.x.ai/v1"

    def test_current_model_validation(self):
        provider = XAIModelProvider("test-key")

        for model_name in (
            "grok-4.5",
            "grok",
            "grok4.5",
            "grok-4.5-latest",
            "grok-build-latest",
        ):
            assert provider.validate_model_name(model_name) is True

        for retired_model in ("grok-3", "grok-4", "grok4", "grok-3-fast", "grok-4-1-fast-reasoning"):
            assert provider.validate_model_name(retired_model) is False

    def test_aliases_resolve_to_grok_4_5(self):
        provider = XAIModelProvider("test-key")

        for alias in (
            "grok",
            "grok4.5",
            "grok-4.5-latest",
            "grok-build-latest",
        ):
            assert provider._resolve_model_name(alias) == "grok-4.5"

    def test_grok_4_5_capabilities(self):
        provider = XAIModelProvider("test-key")
        capabilities = provider.get_capabilities("grok-4.5")

        assert capabilities.model_name == "grok-4.5"
        assert capabilities.friendly_name == "X.AI (Grok 4.5)"
        assert capabilities.context_window == 500_000
        assert capabilities.provider == ProviderType.XAI
        assert capabilities.supports_extended_thinking is True
        assert capabilities.supports_system_prompts is True
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is True
        assert capabilities.supports_images is True
        assert capabilities.allow_code_generation is True
        assert capabilities.use_openai_response_api is True
        assert capabilities.temperature_constraint.min_temp == 0.0
        assert capabilities.temperature_constraint.max_temp == 2.0
        assert capabilities.temperature_constraint.default_temp == 0.3

    def test_capabilities_resolve_supported_aliases(self):
        provider = XAIModelProvider("test-key")

        for alias in ("grok", "grok4.5", "grok-4.5-latest", "grok-build-latest"):
            capabilities = provider.get_capabilities(alias)
            assert capabilities.model_name == "grok-4.5"
            assert capabilities.supports_extended_thinking is True

    def test_unsupported_model_capabilities(self):
        provider = XAIModelProvider("test-key")

        with pytest.raises(ValueError, match="Unsupported model 'grok-3' for provider xai"):
            provider.get_capabilities("grok-3")

    @patch.dict(os.environ, {"XAI_ALLOWED_MODELS": "grok"})
    def test_alias_restriction_allows_alias_only(self):
        import utils.model_restrictions
        from providers.registry import ModelProviderRegistry

        utils.model_restrictions._restriction_service = None
        ModelProviderRegistry.reset_for_testing()
        provider = XAIModelProvider("test-key")

        assert provider.validate_model_name("grok") is True
        assert provider.validate_model_name("grok-4.5") is False

    @patch.dict(os.environ, {"XAI_ALLOWED_MODELS": "grok-4.5"})
    def test_canonical_restriction_allows_alias_resolution(self):
        import utils.model_restrictions
        from providers.registry import ModelProviderRegistry

        utils.model_restrictions._restriction_service = None
        ModelProviderRegistry.reset_for_testing()
        provider = XAIModelProvider("test-key")

        assert provider.validate_model_name("grok-4.5") is True
        assert provider.validate_model_name("grok") is True

    @patch.dict(os.environ, {"XAI_ALLOWED_MODELS": "grok,grok-4.5"})
    def test_alias_and_canonical_restrictions_can_coexist(self):
        import utils.model_restrictions
        from providers.registry import ModelProviderRegistry

        utils.model_restrictions._restriction_service = None
        ModelProviderRegistry.reset_for_testing()
        provider = XAIModelProvider("test-key")

        assert provider.validate_model_name("grok") is True
        assert provider.validate_model_name("grok-4.5") is True
        assert provider.validate_model_name("grok-4") is False

    @patch.dict(os.environ, {"XAI_ALLOWED_MODELS": ""})
    def test_empty_restrictions_allow_current_models_only(self):
        provider = XAIModelProvider("test-key")

        assert provider.validate_model_name("grok-4.5") is True
        assert provider.validate_model_name("grok") is True
        assert provider.validate_model_name("grok-4") is False

    def test_friendly_name(self):
        provider = XAIModelProvider("test-key")

        assert provider.FRIENDLY_NAME == "X.AI"
        assert provider.get_capabilities("grok-4.5").friendly_name == "X.AI (Grok 4.5)"

    def test_supported_models_structure(self):
        from providers.shared import ModelCapabilities

        provider = XAIModelProvider("test-key")

        assert list(provider.MODEL_CAPABILITIES) == ["grok-4.5"]
        assert isinstance(provider.MODEL_CAPABILITIES["grok-4.5"], ModelCapabilities)

    @patch("providers.openai_compatible.OpenAI")
    @pytest.mark.parametrize("alias", ["grok", "grok4.5", "grok-4.5-latest", "grok-build-latest"])
    def test_generate_content_resolves_alias_before_api_call(self, mock_openai_class, alias):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.output_text = "Test response"
        mock_response.model = "grok-4.5"
        mock_response.usage = None
        mock_client.responses.create.return_value = mock_response

        provider = XAIModelProvider("test-key")
        result = provider.generate_content(
            prompt="Test prompt",
            model_name=alias,
            temperature=9.0,
        )

        call_kwargs = mock_client.responses.create.call_args.kwargs
        assert call_kwargs["model"] == "grok-4.5"
        assert call_kwargs["input"] == [{"role": "user", "content": [{"type": "input_text", "text": "Test prompt"}]}]
        assert call_kwargs["reasoning"] == {"effort": "medium"}
        assert call_kwargs["store"] is True
        assert call_kwargs["temperature"] == 2.0
        assert result.content == "Test response"
        assert result.model_name == "grok-4.5"

    def test_current_model_preferences_use_grok_4_5(self):
        from tools.models import ToolModelCategory

        provider = XAIModelProvider("test-key")
        allowed = ["fallback", "grok-4.5"]

        assert provider.get_preferred_model(ToolModelCategory.EXTENDED_REASONING, allowed) == "grok-4.5"
        assert provider.get_preferred_model(ToolModelCategory.FAST_RESPONSE, allowed) == "grok-4.5"
        assert provider.get_preferred_model(ToolModelCategory.BALANCED, allowed) == "grok-4.5"
