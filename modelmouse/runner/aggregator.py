"""
Result Aggregator - Compute aggregate statistics for benchmark runs.

Calculates per-model and overall statistics from benchmark results.
"""
from typing import List, Dict, Optional
from collections import defaultdict

from ..core.schemas import TestResult


def get_result_score(result: TestResult) -> Optional[float]:
    """Get the score for a result.

    Returns overall_score if available, otherwise returns None.
    """
    if result.overall_score is not None:
        return result.overall_score
    return None


def calculate_aggregate_stats(results: List[TestResult]) -> Dict:
    """Calculate aggregate statistics for a benchmark run.

    Computes:
    - total_cost: Sum of all estimated costs
    - avg_latency_ms: Average latency across successful results
    - avg_score: Average score across successful results
    - best_model: Model with highest average score
    - fastest_model: Model with lowest average latency
    - cheapest_model: Model with lowest total cost

    Args:
        results: List of TestResult objects

    Returns:
        Dict of aggregate statistics
    """
    if not results:
        return {}

    stats = {}

    successful_results = [r for r in results if r.success]

    if not successful_results:
        return stats

    costs = [r.estimated_cost for r in successful_results if r.estimated_cost]
    if costs:
        stats["total_cost"] = round(sum(costs), 6)

    latencies = [r.latency_ms for r in successful_results if r.latency_ms]
    if latencies:
        stats["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)

    scores = [get_result_score(r) for r in successful_results]
    scores = [s for s in scores if s is not None]
    if scores:
        stats["avg_score"] = round(sum(scores) / len(scores), 2)

    model_scores = defaultdict(list)
    model_latencies = defaultdict(list)
    model_costs = defaultdict(list)

    for r in successful_results:
        score = get_result_score(r)
        if score is not None:
            model_scores[r.model].append(score)
        if r.latency_ms is not None:
            model_latencies[r.model].append(r.latency_ms)
        if r.estimated_cost is not None:
            model_costs[r.model].append(r.estimated_cost)

    if model_scores:
        best_model = max(
            model_scores.keys(),
            key=lambda m: sum(model_scores[m]) / len(model_scores[m])
        )
        stats["best_model"] = best_model

    if model_latencies:
        fastest_model = min(
            model_latencies.keys(),
            key=lambda m: sum(model_latencies[m]) / len(model_latencies[m])
        )
        stats["fastest_model"] = fastest_model

    if model_costs:
        cheapest_model = min(
            model_costs.keys(),
            key=lambda m: sum(model_costs[m])
        )
        stats["cheapest_model"] = cheapest_model

    return stats


def calculate_per_model_stats(results: List[TestResult]) -> Dict[str, Dict]:
    """Calculate statistics for each model.

    Args:
        results: List of TestResult objects

    Returns:
        Dict mapping model ID to its statistics:
        {
            "model_id": {
                "total_tests": int,
                "successful_tests": int,
                "avg_score": float,
                "avg_latency_ms": float,
                "total_cost": float,
                "success_rate": float (0-100),
            }
        }
    """
    model_stats = {}

    model_results = defaultdict(list)
    for r in results:
        model_results[r.model].append(r)

    for model_id, model_result_list in model_results.items():
        successful = [r for r in model_result_list if r.success]
        total = len(model_result_list)
        successful_count = len(successful)

        stats = {
            "total_tests": total,
            "successful_tests": successful_count,
            "success_rate": round((successful_count / total * 100), 2) if total > 0 else 0.0,
        }

        if successful:
            scores = [get_result_score(r) for r in successful]
            scores = [s for s in scores if s is not None]
            if scores:
                stats["avg_score"] = round(sum(scores) / len(scores), 2)

            latencies = [r.latency_ms for r in successful if r.latency_ms]
            if latencies:
                stats["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)

            costs = [r.estimated_cost for r in successful if r.estimated_cost]
            if costs:
                stats["total_cost"] = round(sum(costs), 6)

        model_stats[model_id] = stats

    return model_stats


def calculate_per_test_stats(results: List[TestResult]) -> Dict[str, Dict]:
    """Calculate statistics for each test case.

    Args:
        results: List of TestResult objects

    Returns:
        Dict mapping test name to its statistics:
        {
            "test_name": {
                "total_models": int,
                "successful_models": int,
                "avg_score": float,
                "avg_latency_ms": float,
                "best_model": str,
                "success_rate": float (0-100),
            }
        }
    """
    test_stats = {}

    test_results = defaultdict(list)
    for r in results:
        test_name = r.test_name or "Unnamed Test"
        test_results[test_name].append(r)

    for test_name, test_result_list in test_results.items():
        successful = [r for r in test_result_list if r.success]
        total = len(test_result_list)
        successful_count = len(successful)

        stats = {
            "total_models": total,
            "successful_models": successful_count,
            "success_rate": round((successful_count / total * 100), 2) if total > 0 else 0.0,
        }

        if successful:
            scores = [get_result_score(r) for r in successful]
            scores = [s for s in scores if s is not None]
            if scores:
                stats["avg_score"] = round(sum(scores) / len(scores), 2)

            latencies = [r.latency_ms for r in successful if r.latency_ms]
            if latencies:
                stats["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)

            model_scores = defaultdict(list)
            for r in successful:
                score = get_result_score(r)
                if score is not None:
                    model_scores[r.model].append(score)

            if model_scores:
                best_model = max(
                    model_scores.keys(),
                    key=lambda m: sum(model_scores[m]) / len(model_scores[m])
                )
                stats["best_model"] = best_model

        test_stats[test_name] = stats

    return test_stats


def rank_models_by_metric(
    results: List[TestResult],
    metric: str = "score"
) -> List[tuple]:
    """Rank models by a specific metric.

    Args:
        results: List of TestResult objects
        metric: Metric to rank by ("score", "latency", "cost", "success_rate")

    Returns:
        List of tuples (model_id, metric_value) sorted by metric
    """
    model_stats = calculate_per_model_stats(results)

    if metric == "score":
        # Higher is better
        ranked = sorted(
            model_stats.items(),
            key=lambda x: x[1].get("avg_score", 0.0),
            reverse=True
        )
        return [(m, s.get("avg_score")) for m, s in ranked]

    elif metric == "latency":
        # Lower is better
        ranked = sorted(
            model_stats.items(),
            key=lambda x: x[1].get("avg_latency_ms", float('inf'))
        )
        return [(m, s.get("avg_latency_ms")) for m, s in ranked]

    elif metric == "cost":
        # Lower is better
        ranked = sorted(
            model_stats.items(),
            key=lambda x: x[1].get("total_cost", float('inf'))
        )
        return [(m, s.get("total_cost")) for m, s in ranked]

    elif metric == "success_rate":
        # Higher is better
        ranked = sorted(
            model_stats.items(),
            key=lambda x: x[1].get("success_rate", 0.0),
            reverse=True
        )
        return [(m, s.get("success_rate")) for m, s in ranked]

    else:
        raise ValueError(f"Unknown metric: {metric}")


def format_summary_report(results: List[TestResult]) -> str:
    """Generate a formatted text summary of benchmark results.

    Args:
        results: List of TestResult objects

    Returns:
        Formatted string summary
    """
    agg_stats = calculate_aggregate_stats(results)
    per_model_stats = calculate_per_model_stats(results)

    lines = []
    lines.append("=" * 60)
    lines.append("BENCHMARK SUMMARY")
    lines.append("=" * 60)
    lines.append("")

    lines.append("Overall Statistics:")
    lines.append(f"  Total Tests Run: {len(results)}")
    lines.append(f"  Successful Tests: {sum(1 for r in results if r.success)}")
    if "avg_score" in agg_stats:
        lines.append(f"  Average Score: {agg_stats['avg_score']:.2f}")
    if "avg_latency_ms" in agg_stats:
        lines.append(f"  Average Latency: {agg_stats['avg_latency_ms']:.2f} ms")
    if "total_cost" in agg_stats:
        lines.append(f"  Total Cost: ${agg_stats['total_cost']:.6f}")
    lines.append("")

    if "best_model" in agg_stats:
        lines.append(f"Best Model (Score): {agg_stats['best_model']}")
    if "fastest_model" in agg_stats:
        lines.append(f"Fastest Model: {agg_stats['fastest_model']}")
    if "cheapest_model" in agg_stats:
        lines.append(f"Cheapest Model: {agg_stats['cheapest_model']}")
    lines.append("")

    lines.append("Per-Model Results:")
    lines.append("-" * 60)
    for model_id in sorted(per_model_stats.keys()):
        stats = per_model_stats[model_id]
        lines.append(f"\n{model_id}:")
        lines.append(f"  Tests: {stats['successful_tests']}/{stats['total_tests']}")
        lines.append(f"  Success Rate: {stats['success_rate']:.1f}%")
        if "avg_score" in stats:
            lines.append(f"  Avg Score: {stats['avg_score']:.2f}")
        if "avg_latency_ms" in stats:
            lines.append(f"  Avg Latency: {stats['avg_latency_ms']:.2f} ms")
        if "total_cost" in stats:
            lines.append(f"  Total Cost: ${stats['total_cost']:.6f}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
