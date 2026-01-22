"""
Pricing utilities for calculating model costs.

Extracted from backend router_service.py for standalone CLI usage.
"""
from typing import Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a model including cost rates."""
    id: str
    name: str
    provider: str
    input_cost_per_1k: float  # $ per 1000 input tokens
    output_cost_per_1k: float  # $ per 1000 output tokens


# Model configurations with pricing (as of Jan 2025)
MODEL_CONFIGS = {
    # Anthropic models - Claude 4.5 series
    "claude-sonnet-4-5-20250929": ModelConfig(
        id="claude-sonnet-4-5-20250929",
        name="Claude Sonnet 4.5",
        provider="anthropic",
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
    ),
    "claude-haiku-4-5-20251001": ModelConfig(
        id="claude-haiku-4-5-20251001",
        name="Claude Haiku 4.5",
        provider="anthropic",
        input_cost_per_1k=0.001,
        output_cost_per_1k=0.005,
    ),
    "claude-opus-4-5-20251101": ModelConfig(
        id="claude-opus-4-5-20251101",
        name="Claude Opus 4.5",
        provider="anthropic",
        input_cost_per_1k=0.005,
        output_cost_per_1k=0.025,
    ),
    # Anthropic models - Claude 4 series
    "claude-sonnet-4-20250514": ModelConfig(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        provider="anthropic",
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
    ),
    # Anthropic models - Claude 3.5 series
    "claude-3-5-haiku-20241022": ModelConfig(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        provider="anthropic",
        input_cost_per_1k=0.0008,
        output_cost_per_1k=0.004,
    ),
    # Anthropic models - Claude 3 series
    "claude-3-haiku-20240307": ModelConfig(
        id="claude-3-haiku-20240307",
        name="Claude 3 Haiku",
        provider="anthropic",
        input_cost_per_1k=0.00025,
        output_cost_per_1k=0.00125,
    ),
    # Google models
    "gemini-2.5-pro": ModelConfig(
        id="gemini-2.5-pro",
        name="Gemini 2.5 Pro",
        provider="google",
        input_cost_per_1k=0.00125,
        output_cost_per_1k=0.005,
    ),
    "gemini-2.5-flash": ModelConfig(
        id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        provider="google",
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
    ),
    "gemini-2.0-flash": ModelConfig(
        id="gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        provider="google",
        input_cost_per_1k=0.0001,
        output_cost_per_1k=0.0004,
    ),
    # OpenAI models
    "gpt-4o": ModelConfig(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        input_cost_per_1k=0.0025,
        output_cost_per_1k=0.01,
    ),
    "gpt-4o-mini": ModelConfig(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
    ),
    "gpt-4-turbo": ModelConfig(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03,
    ),
    "gpt-3.5-turbo": ModelConfig(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.0015,
    ),
    # Mistral models
    "mistral-large-latest": ModelConfig(
        id="mistral-large-latest",
        name="Mistral Large",
        provider="mistral",
        input_cost_per_1k=0.002,
        output_cost_per_1k=0.006,
    ),
    "mistral-medium-latest": ModelConfig(
        id="mistral-medium-latest",
        name="Mistral Medium",
        provider="mistral",
        input_cost_per_1k=0.00275,
        output_cost_per_1k=0.0081,
    ),
    "mistral-small-latest": ModelConfig(
        id="mistral-small-latest",
        name="Mistral Small",
        provider="mistral",
        input_cost_per_1k=0.0002,
        output_cost_per_1k=0.0006,
    ),
    "pixtral-large-latest": ModelConfig(
        id="pixtral-large-latest",
        name="Pixtral Large",
        provider="mistral",
        input_cost_per_1k=0.002,
        output_cost_per_1k=0.006,
    ),
    "pixtral-12b-latest": ModelConfig(
        id="pixtral-12b-latest",
        name="Pixtral 12B",
        provider="mistral",
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.00015,
    ),
    "codestral-latest": ModelConfig(
        id="codestral-latest",
        name="Codestral",
        provider="mistral",
        input_cost_per_1k=0.0003,
        output_cost_per_1k=0.0009,
    ),
    # DeepSeek models
    "deepseek-chat": ModelConfig(
        id="deepseek-chat",
        name="DeepSeek Chat (V3)",
        provider="deepseek",
        input_cost_per_1k=0.00014,
        output_cost_per_1k=0.00028,
    ),
    "deepseek-reasoner": ModelConfig(
        id="deepseek-reasoner",
        name="DeepSeek Reasoner (R1)",
        provider="deepseek",
        input_cost_per_1k=0.00055,
        output_cost_per_1k=0.00219,
    ),
    "deepseek-coder": ModelConfig(
        id="deepseek-coder",
        name="DeepSeek Coder",
        provider="deepseek",
        input_cost_per_1k=0.00014,
        output_cost_per_1k=0.00028,
    ),
    # Groq models - pricing per 1M tokens converted to per 1K
    # GPT OSS models (structured output support)
    "openai/gpt-oss-120b": ModelConfig(
        id="openai/gpt-oss-120b",
        name="GPT OSS 120B",
        provider="groq",
        input_cost_per_1k=0.00015,  # $0.15/M
        output_cost_per_1k=0.00060,  # $0.60/M
    ),
    "openai/gpt-oss-20b": ModelConfig(
        id="openai/gpt-oss-20b",
        name="GPT OSS 20B",
        provider="groq",
        input_cost_per_1k=0.000075,  # $0.075/M
        output_cost_per_1k=0.00030,  # $0.30/M
    ),
    # Llama 4 Vision models (structured output + vision)
    "meta-llama/llama-4-scout-17b-16e-instruct": ModelConfig(
        id="meta-llama/llama-4-scout-17b-16e-instruct",
        name="Llama 4 Scout",
        provider="groq",
        input_cost_per_1k=0.00011,  # $0.11/M
        output_cost_per_1k=0.00034,  # $0.34/M
    ),
    "meta-llama/llama-4-maverick-17b-128e-instruct": ModelConfig(
        id="meta-llama/llama-4-maverick-17b-128e-instruct",
        name="Llama 4 Maverick",
        provider="groq",
        input_cost_per_1k=0.00020,  # $0.20/M
        output_cost_per_1k=0.00060,  # $0.60/M
    ),
    # Llama 3.x models (json_object mode)
    "llama-3.3-70b-versatile": ModelConfig(
        id="llama-3.3-70b-versatile",
        name="Llama 3.3 70B Versatile",
        provider="groq",
        input_cost_per_1k=0.00059,  # $0.59/M
        output_cost_per_1k=0.00079,  # $0.79/M
    ),
    "llama-3.1-8b-instant": ModelConfig(
        id="llama-3.1-8b-instant",
        name="Llama 3.1 8B Instant",
        provider="groq",
        input_cost_per_1k=0.00005,  # $0.05/M
        output_cost_per_1k=0.00008,  # $0.08/M
    ),
    # Qwen (structured output support)
    "qwen/qwen3-32b": ModelConfig(
        id="qwen/qwen3-32b",
        name="Qwen3 32B",
        provider="groq",
        input_cost_per_1k=0.00029,  # $0.29/M
        output_cost_per_1k=0.00059,  # $0.59/M
    ),
}


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost for a request given token counts.

    Args:
        model_id: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in dollars
    """
    config = MODEL_CONFIGS.get(model_id)
    if not config:
        return 0.0
    input_cost = (input_tokens / 1000) * config.input_cost_per_1k
    output_cost = (output_tokens / 1000) * config.output_cost_per_1k
    return round(input_cost + output_cost, 6)


def get_model_info(model_id: str) -> Optional[ModelConfig]:
    """Get pricing and metadata for a model.

    Args:
        model_id: Model identifier

    Returns:
        ModelConfig if found, None otherwise
    """
    return MODEL_CONFIGS.get(model_id)
