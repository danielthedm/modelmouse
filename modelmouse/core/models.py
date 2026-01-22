from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Model information."""
    model_id: str
    provider: str
    display_name: str
    supports_vision: bool = False
    supports_json_schema: bool = False
    context_window: int = 0
    max_output_tokens: int = 0


ANTHROPIC_MODELS = [
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-5-20251101",
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307",
]

OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

GOOGLE_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

MISTRAL_MODELS = [
    "mistral-large-latest",
    "mistral-medium-latest",
    "mistral-small-latest",
    "ministral-8b-latest",
    "ministral-3b-latest",
    "codestral-latest",
    "pixtral-large-latest",
    "pixtral-12b-latest",
    "open-mistral-nemo",
    "open-mixtral-8x22b",
    "open-mixtral-8x7b",
]

DEEPSEEK_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-coder",
]

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
]

MODEL_CATALOG: Dict[str, ModelInfo] = {
    "claude-sonnet-4-5-20250929": ModelInfo(
        model_id="claude-sonnet-4-5-20250929",
        provider="anthropic",
        display_name="Sonnet 4.5",
        supports_vision=True,
        supports_json_schema=True,
        context_window=200000,
        max_output_tokens=8192,
    ),
    "claude-haiku-4-5-20251001": ModelInfo(
        model_id="claude-haiku-4-5-20251001",
        provider="anthropic",
        display_name="Haiku 4.5",
        supports_vision=True,
        supports_json_schema=True,
        context_window=200000,
        max_output_tokens=8192,
    ),
    "claude-opus-4-5-20251101": ModelInfo(
        model_id="claude-opus-4-5-20251101",
        provider="anthropic",
        display_name="Opus 4.5",
        supports_vision=True,
        supports_json_schema=True,
        context_window=200000,
        max_output_tokens=16384,
    ),
    "claude-sonnet-4-20250514": ModelInfo(
        model_id="claude-sonnet-4-20250514",
        provider="anthropic",
        display_name="Sonnet 4",
        supports_vision=True,
        supports_json_schema=True,
        context_window=200000,
        max_output_tokens=8192,
    ),
    "claude-3-5-haiku-20241022": ModelInfo(
        model_id="claude-3-5-haiku-20241022",
        provider="anthropic",
        display_name="Haiku 3.5",
        supports_vision=True,
        supports_json_schema=True,
        context_window=200000,
        max_output_tokens=8192,
    ),
    "claude-3-haiku-20240307": ModelInfo(
        model_id="claude-3-haiku-20240307",
        provider="anthropic",
        display_name="Haiku 3",
        supports_vision=True,
        supports_json_schema=True,
        context_window=200000,
        max_output_tokens=4096,
    ),
    "gpt-4o": ModelInfo(
        model_id="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        supports_vision=True,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=16384,
    ),
    "gpt-4o-mini": ModelInfo(
        model_id="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        supports_vision=True,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=16384,
    ),
    "gpt-4-turbo": ModelInfo(
        model_id="gpt-4-turbo",
        provider="openai",
        display_name="GPT-4 Turbo",
        supports_vision=True,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=4096,
    ),
    "gpt-3.5-turbo": ModelInfo(
        model_id="gpt-3.5-turbo",
        provider="openai",
        display_name="GPT-3.5 Turbo",
        supports_vision=False,
        supports_json_schema=True,
        context_window=16385,
        max_output_tokens=4096,
    ),
    "gemini-2.5-pro": ModelInfo(
        model_id="gemini-2.5-pro",
        provider="google",
        display_name="Gemini 2.5 Pro",
        supports_vision=True,
        supports_json_schema=True,
        context_window=2000000,
        max_output_tokens=8192,
    ),
    "gemini-2.5-flash": ModelInfo(
        model_id="gemini-2.5-flash",
        provider="google",
        display_name="Gemini 2.5 Flash",
        supports_vision=True,
        supports_json_schema=True,
        context_window=1000000,
        max_output_tokens=8192,
    ),
    "gemini-2.0-flash": ModelInfo(
        model_id="gemini-2.0-flash",
        provider="google",
        display_name="Gemini 2.0 Flash",
        supports_vision=True,
        supports_json_schema=True,
        context_window=1000000,
        max_output_tokens=8192,
    ),
    "mistral-large-latest": ModelInfo(
        model_id="mistral-large-latest",
        provider="mistral",
        display_name="Mistral Large",
        supports_vision=False,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=4096,
    ),
    "mistral-medium-latest": ModelInfo(
        model_id="mistral-medium-latest",
        provider="mistral",
        display_name="Mistral Medium",
        supports_vision=False,
        supports_json_schema=True,
        context_window=32000,
        max_output_tokens=4096,
    ),
    "mistral-small-latest": ModelInfo(
        model_id="mistral-small-latest",
        provider="mistral",
        display_name="Mistral Small",
        supports_vision=False,
        supports_json_schema=True,
        context_window=32000,
        max_output_tokens=4096,
    ),
    "ministral-8b-latest": ModelInfo(
        model_id="ministral-8b-latest",
        provider="mistral",
        display_name="Ministral 8B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=4096,
    ),
    "ministral-3b-latest": ModelInfo(
        model_id="ministral-3b-latest",
        provider="mistral",
        display_name="Ministral 3B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=4096,
    ),
    "codestral-latest": ModelInfo(
        model_id="codestral-latest",
        provider="mistral",
        display_name="Codestral",
        supports_vision=False,
        supports_json_schema=True,
        context_window=32000,
        max_output_tokens=4096,
    ),
    "pixtral-large-latest": ModelInfo(
        model_id="pixtral-large-latest",
        provider="mistral",
        display_name="Pixtral Large",
        supports_vision=True,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=4096,
    ),
    "pixtral-12b-latest": ModelInfo(
        model_id="pixtral-12b-latest",
        provider="mistral",
        display_name="Pixtral 12B",
        supports_vision=True,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=4096,
    ),
    "open-mistral-nemo": ModelInfo(
        model_id="open-mistral-nemo",
        provider="mistral",
        display_name="Open Mistral Nemo",
        supports_vision=False,
        supports_json_schema=False,
        context_window=128000,
        max_output_tokens=4096,
    ),
    "open-mixtral-8x22b": ModelInfo(
        model_id="open-mixtral-8x22b",
        provider="mistral",
        display_name="Open Mixtral 8x22B",
        supports_vision=False,
        supports_json_schema=False,
        context_window=64000,
        max_output_tokens=4096,
    ),
    "open-mixtral-8x7b": ModelInfo(
        model_id="open-mixtral-8x7b",
        provider="mistral",
        display_name="Open Mixtral 8x7B",
        supports_vision=False,
        supports_json_schema=False,
        context_window=32000,
        max_output_tokens=4096,
    ),
    "deepseek-chat": ModelInfo(
        model_id="deepseek-chat",
        provider="deepseek",
        display_name="DeepSeek Chat",
        supports_vision=False,
        supports_json_schema=True,
        context_window=64000,
        max_output_tokens=8192,
    ),
    "deepseek-reasoner": ModelInfo(
        model_id="deepseek-reasoner",
        provider="deepseek",
        display_name="DeepSeek Reasoner",
        supports_vision=False,
        supports_json_schema=True,
        context_window=64000,
        max_output_tokens=8192,
    ),
    "deepseek-coder": ModelInfo(
        model_id="deepseek-coder",
        provider="deepseek",
        display_name="DeepSeek Coder",
        supports_vision=False,
        supports_json_schema=True,
        context_window=64000,
        max_output_tokens=8192,
    ),
    "openai/gpt-oss-120b": ModelInfo(
        model_id="openai/gpt-oss-120b",
        provider="groq",
        display_name="GPT OSS 120B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=32768,
        max_output_tokens=32768,
    ),
    "openai/gpt-oss-20b": ModelInfo(
        model_id="openai/gpt-oss-20b",
        provider="groq",
        display_name="GPT OSS 20B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=32768,
        max_output_tokens=32768,
    ),
    "meta-llama/llama-4-scout-17b-16e-instruct": ModelInfo(
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        provider="groq",
        display_name="Llama 4 Scout 17B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=8192,
    ),
    "meta-llama/llama-4-maverick-17b-128e-instruct": ModelInfo(
        model_id="meta-llama/llama-4-maverick-17b-128e-instruct",
        provider="groq",
        display_name="Llama 4 Maverick 17B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=8192,
    ),
    "llama-3.3-70b-versatile": ModelInfo(
        model_id="llama-3.3-70b-versatile",
        provider="groq",
        display_name="Llama 3.3 70B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=32768,
    ),
    "llama-3.1-8b-instant": ModelInfo(
        model_id="llama-3.1-8b-instant",
        provider="groq",
        display_name="Llama 3.1 8B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=128000,
        max_output_tokens=8000,
    ),
    "qwen/qwen3-32b": ModelInfo(
        model_id="qwen/qwen3-32b",
        provider="groq",
        display_name="Qwen 3 32B",
        supports_vision=False,
        supports_json_schema=True,
        context_window=32768,
        max_output_tokens=32768,
    ),
}


def get_models_by_provider(provider: str) -> List[str]:
    """Get all model IDs for a specific provider."""
    provider_map = {
        "anthropic": ANTHROPIC_MODELS,
        "openai": OPENAI_MODELS,
        "google": GOOGLE_MODELS,
        "mistral": MISTRAL_MODELS,
        "deepseek": DEEPSEEK_MODELS,
        "groq": GROQ_MODELS,
    }
    return provider_map.get(provider.lower(), [])


def get_all_models() -> List[str]:
    """Get all available model IDs."""
    return list(MODEL_CATALOG.keys())


def get_model_info(model_id: str) -> ModelInfo:
    """Get information about a specific model."""
    return MODEL_CATALOG.get(model_id)


def get_provider_for_model(model_id: str) -> str:
    """Get the provider name for a given model ID."""
    model_info = MODEL_CATALOG.get(model_id)
    if model_info:
        return model_info.provider
    return None
