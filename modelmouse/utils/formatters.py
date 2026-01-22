import json
from typing import Any, Dict, List
from tabulate import tabulate


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as pretty JSON."""
    return json.dumps(data, indent=indent, default=str)


def format_table(
    data: List[Dict[str, Any]],
    headers: List[str],
    tablefmt: str = "grid"
) -> str:
    """Format data as a table."""
    rows = []
    for item in data:
        row = [item.get(h, "") for h in headers]
        rows.append(row)

    return tabulate(rows, headers=headers, tablefmt=tablefmt)


def format_results_table(results: List[Dict[str, Any]]) -> str:
    """Format benchmark results as a table."""
    headers = ["Model", "Test", "Score", "Latency (ms)", "Cost ($)", "Success"]

    rows = []
    for r in results:
        rows.append([
            r.get("model", ""),
            r.get("test_name", "")[:30],
            f"{r.get('overall_score', 0):.1f}",
            f"{r.get('latency_ms', 0):.0f}",
            f"{r.get('estimated_cost', 0):.4f}",
            "✓" if r.get("success") else "✗"
        ])

    return tabulate(rows, headers=headers, tablefmt="grid")


def format_summary(summary: Dict[str, Any]) -> str:
    """Format benchmark summary statistics."""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("BENCHMARK SUMMARY")
    lines.append("=" * 60)

    if "total_cost" in summary:
        lines.append(f"Total Cost: ${summary['total_cost']:.4f}")
    if "avg_latency_ms" in summary:
        lines.append(f"Average Latency: {summary['avg_latency_ms']:.0f} ms")
    if "avg_score" in summary:
        lines.append(f"Average Score: {summary['avg_score']:.1f}/100")

    lines.append("\nTop Performers:")
    if "best_model" in summary:
        lines.append(f"  Best Model: {summary['best_model']}")
    if "fastest_model" in summary:
        lines.append(f"  Fastest Model: {summary['fastest_model']}")
    if "cheapest_model" in summary:
        lines.append(f"  Cheapest Model: {summary['cheapest_model']}")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_model_list(models: List[Dict[str, Any]]) -> str:
    """Format model list for display."""
    headers = ["Model ID", "Provider", "Vision", "JSON Schema", "Context"]

    rows = []
    for m in models:
        rows.append([
            m["model_id"],
            m["provider"],
            "✓" if m.get("supports_vision") else "✗",
            "✓" if m.get("supports_json_schema") else "✗",
            f"{m.get('context_window', 0):,}" if m.get("context_window") else "N/A"
        ])

    return tabulate(rows, headers=headers, tablefmt="grid")


def format_recommendations(recommendations: List[Dict[str, Any]], reasoning: str) -> str:
    """Format model recommendations."""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("MODEL RECOMMENDATIONS")
    lines.append("=" * 60)
    lines.append(f"\n{reasoning}\n")

    for i, rec in enumerate(recommendations, 1):
        lines.append(f"{i}. {rec['model_id']} ({rec['confidence'].upper()} confidence)")
        lines.append(f"   {rec['reasoning']}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_csv(data: List[Dict[str, Any]], headers: List[str]) -> str:
    """Format data as CSV."""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


def format_leaderboard(results: List[Dict[str, Any]], benchmark_type: str = "schematized") -> str:
    """
    Format results as a ranked leaderboard table showing models, presets, and scores.
    Similar to modelator.ai results page.
    """
    from collections import defaultdict

    model_stats = defaultdict(lambda: {
        'scores': [],
        'judge_scores': [],
        'latencies': [],
        'costs': [],
        'presets': set(),
        'successes': 0,
        'total': 0
    })

    for r in results:
        model = r.get('model', 'unknown')
        preset = r.get('preset_name', r.get('preset', 'default'))

        model_stats[model]['presets'].add(preset)
        model_stats[model]['total'] += 1

        if r.get('success'):
            model_stats[model]['successes'] += 1

        if r.get('overall_score') is not None:
            model_stats[model]['scores'].append(r['overall_score'])

        if r.get('judge_score') is not None:
            model_stats[model]['judge_scores'].append(r['judge_score'])

        if r.get('latency_ms') is not None:
            model_stats[model]['latencies'].append(r['latency_ms'])

        if r.get('estimated_cost') is not None:
            model_stats[model]['costs'].append(r['estimated_cost'])

    leaderboard = []
    for model, stats in model_stats.items():
        avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
        avg_judge = sum(stats['judge_scores']) / len(stats['judge_scores']) if stats['judge_scores'] else None
        avg_latency = sum(stats['latencies']) / len(stats['latencies']) if stats['latencies'] else 0
        total_cost = sum(stats['costs']) if stats['costs'] else 0
        success_rate = (stats['successes'] / stats['total'] * 100) if stats['total'] > 0 else 0

        leaderboard.append({
            'model': model,
            'avg_score': avg_score,
            'avg_judge': avg_judge,
            'avg_latency': avg_latency,
            'total_cost': total_cost,
            'success_rate': success_rate,
            'presets': ', '.join(sorted(stats['presets'])),
            'tests': stats['total']
        })

    # For unschematized benchmarks, sort by AI Judge score if available
    has_judge_scores = any(x['avg_judge'] is not None and x['avg_judge'] > 0 for x in leaderboard)

    if benchmark_type == "unschematized" and has_judge_scores:
        leaderboard.sort(key=lambda x: x['avg_judge'] if x['avg_judge'] is not None else 0, reverse=True)
        score_column = "AI Judge"
    else:
        leaderboard.sort(key=lambda x: x['avg_score'], reverse=True)
        score_column = "Avg Score"

    lines = []
    lines.append("\nModel Rankings by " + score_column)
    lines.append("")

    # Build table rows
    headers = ["Rank", "Model", score_column, "Speed (ms)", "Cost ($)", "Success %", "Tests", "Presets"]
    rows = []

    for i, entry in enumerate(leaderboard, 1):
        rank = str(i)

        # Choose which score to display
        if benchmark_type == "unschematized" and has_judge_scores:
            score_val = entry['avg_judge'] if entry['avg_judge'] is not None else 0
        else:
            score_val = entry['avg_score']

        rows.append([
            rank,
            entry['model'],
            f"{score_val:.2f}",
            f"{entry['avg_latency']:.0f}",
            f"${entry['total_cost']:.4f}",
            f"{entry['success_rate']:.0f}%",
            str(entry['tests']),
            entry['presets'][:30]
        ])

    lines.append(tabulate(rows, headers=headers, tablefmt="simple"))
    lines.append("")

    return "\n".join(lines)


def format_detailed_results(results: List[Dict[str, Any]], group_by: str = "model") -> str:
    """
    Format detailed results table grouped by model or test.
    Shows individual test results with preset information.
    """
    from collections import defaultdict

    if group_by == "model":
        grouped = defaultdict(list)
        for r in results:
            grouped[r.get('model', 'unknown')].append(r)
    else:
        grouped = defaultdict(list)
        for r in results:
            grouped[r.get('test_name', 'unknown')].append(r)

    lines = []
    lines.append("\n" + "=" * 120)
    lines.append(f"DETAILED RESULTS (Grouped by {group_by.title()})")
    lines.append("=" * 120 + "\n")

    for group_name, group_results in grouped.items():
        lines.append(f"\n{group_name}")
        lines.append("-" * 80)

        headers = ["Test", "Preset", "Score", "Latency", "Cost", "Status"]
        rows = []

        for r in group_results:
            score_display = f"{r.get('overall_score', 0):.1f}"
            if r.get('judge_score'):
                score_display = f"{r.get('overall_score', 0):.1f} / {r.get('judge_score'):.1f}★"

            rows.append([
                r.get('test_name', '')[:30],
                r.get('preset_name', '')[:20],
                score_display,
                f"{r.get('latency_ms', 0):.0f}ms",
                f"${r.get('estimated_cost', 0):.4f}",
                "✓" if r.get('success') else "✗"
            ])

        lines.append(tabulate(rows, headers=headers, tablefmt="simple"))

    lines.append("\n" + "=" * 120)
    return "\n".join(lines)
