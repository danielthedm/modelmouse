"""
Benchmark runner modules for CLI execution.

Extracted from backend for standalone usage without database dependencies.
"""
from .executor import run_benchmark, run_single_test, run_tests_against_models
from .aggregator import (
    calculate_aggregate_stats,
    calculate_per_model_stats,
    calculate_per_test_stats,
    rank_models_by_metric,
    format_summary_report,
)
from .progress import BenchmarkProgress, LiveBenchmarkDisplay, create_progress_callback

__all__ = [
    # Main execution
    "run_benchmark",
    "run_single_test",
    "run_tests_against_models",
    # Aggregation
    "calculate_aggregate_stats",
    "calculate_per_model_stats",
    "calculate_per_test_stats",
    "rank_models_by_metric",
    "format_summary_report",
    # Progress display
    "BenchmarkProgress",
    "LiveBenchmarkDisplay",
    "create_progress_callback",
]
