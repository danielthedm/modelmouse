"""Tests for model catalog."""
import pytest
from modelmouse.core.models import (
    MODEL_CATALOG,
    get_all_models,
    get_models_by_provider,
    get_model_info,
    get_provider_for_model,
)


class TestModelCatalog:
    def test_catalog_not_empty(self):
        assert len(MODEL_CATALOG) > 0

    def test_all_models_have_required_fields(self):
        for model_id, info in MODEL_CATALOG.items():
            assert info.model_id == model_id
            assert info.provider
            assert info.display_name
            assert isinstance(info.supports_vision, bool)
            assert isinstance(info.supports_json_schema, bool)

    def test_get_all_models(self):
        models = get_all_models()
        assert len(models) >= 34
        assert "claude-sonnet-4-5-20250929" in models

    def test_get_models_by_provider(self):
        anthropic_models = get_models_by_provider("anthropic")
        assert len(anthropic_models) >= 6
        assert all("claude" in m for m in anthropic_models)

        openai_models = get_models_by_provider("openai")
        assert len(openai_models) >= 3
        assert "gpt-4o" in openai_models

    def test_get_model_info(self):
        info = get_model_info("claude-sonnet-4-5-20250929")
        assert info is not None
        assert info.provider == "anthropic"
        assert info.supports_vision is True

    def test_get_provider_for_model(self):
        assert get_provider_for_model("claude-sonnet-4-5-20250929") == "anthropic"
        assert get_provider_for_model("gpt-4o") == "openai"
        assert get_provider_for_model("gemini-2.5-pro") == "google"

    def test_vision_models(self):
        vision_models = [
            model_id for model_id, info in MODEL_CATALOG.items()
            if info.supports_vision
        ]
        assert len(vision_models) >= 14
        assert "claude-sonnet-4-5-20250929" in vision_models
        assert "gpt-4o" in vision_models
        assert "gemini-2.5-pro" in vision_models
