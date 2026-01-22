from .types import BenchmarkMode

QUICK_CONFIGS = [
    {
        "name": "Deterministic",
        "key": "deterministic",
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 2048,
    }
]

STANDARD_CONFIGS = [
    {
        "name": "Temp 0",
        "key": "temp_0",
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 2048,
    },
    {
        "name": "Temp 0.5",
        "key": "temp_0.5",
        "temperature": 0.5,
        "top_p": 1.0,
        "max_tokens": 2048,
    },
    {
        "name": "Temp 1.0",
        "key": "temp_1.0",
        "temperature": 1.0,
        "top_p": 1.0,
        "max_tokens": 2048,
    },
]

DEFAULT_SWEEP_CONFIGS = [
    {"name": "Temp 0", "key": "sweep_t0", "temperature": 0.0, "top_p": 1.0, "max_tokens": 2048},
    {"name": "Temp 0.3", "key": "sweep_t0.3", "temperature": 0.3, "top_p": 1.0, "max_tokens": 2048},
    {"name": "Temp 0.5", "key": "sweep_t0.5", "temperature": 0.5, "top_p": 1.0, "max_tokens": 2048},
    {"name": "Temp 0.7", "key": "sweep_t0.7", "temperature": 0.7, "top_p": 1.0, "max_tokens": 2048},
    {"name": "Temp 1.0", "key": "sweep_t1.0", "temperature": 1.0, "top_p": 1.0, "max_tokens": 2048},
]

SWEEPABLE_PARAMETERS = {
    "temperature": {
        "name": "Temperature",
        "description": "Controls randomness (0=deterministic, 1=creative)",
        "type": "float",
        "min": 0.0,
        "max": 2.0,
        "default_values": [0.0, 0.3, 0.5, 0.7, 1.0],
    },
    "top_p": {
        "name": "Top P",
        "description": "Nucleus sampling threshold",
        "type": "float",
        "min": 0.0,
        "max": 1.0,
        "default_values": [0.9, 0.95, 1.0],
    },
    "top_k": {
        "name": "Top K",
        "description": "Limit to top K tokens",
        "type": "int",
        "min": 1,
        "max": 100,
        "default_values": [10, 40, 100],
    },
    "frequency_penalty": {
        "name": "Frequency Penalty",
        "description": "Penalize repeated tokens",
        "type": "float",
        "min": -2.0,
        "max": 2.0,
        "default_values": [0.0, 0.5, 1.0],
    },
    "presence_penalty": {
        "name": "Presence Penalty",
        "description": "Penalize tokens already in context",
        "type": "float",
        "min": -2.0,
        "max": 2.0,
        "default_values": [0.0, 0.5, 1.0],
    },
}

SWEEP_TOP_N_MODELS = 3


def get_mode_configs(mode: BenchmarkMode) -> list:
    """Get parameter configurations for a benchmark mode."""
    if mode == BenchmarkMode.QUICK:
        return QUICK_CONFIGS
    elif mode == BenchmarkMode.STANDARD:
        return STANDARD_CONFIGS
    else:
        return []
