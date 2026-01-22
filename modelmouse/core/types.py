from enum import Enum


class BenchmarkMode(str, Enum):
    """Benchmark testing mode."""
    QUICK = "quick"
    STANDARD = "standard"
    SWEEP = "sweep"


class BenchmarkType(str, Enum):
    """Benchmark output type."""
    SCHEMATIZED = "schematized"
    UNSCHEMATIZED = "unschematized"


class EvaluationMode(str, Enum):
    """How to evaluate benchmark results."""
    SCHEMA_MATCH = "schema_match"
    AI_JUDGE = "ai_judge"
