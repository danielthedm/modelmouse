"""
Benchmark Executor - Main benchmark execution logic extracted from backend.

Runs tests against models without database dependencies. Designed for CLI usage.
"""
from typing import List, Dict, Optional, Any, Callable, Set, Tuple
import time
import itertools
from datetime import datetime

from ..core.schemas import BenchmarkConfig, TestCase, TestResult, BenchmarkRun
from ..core.types import BenchmarkMode, BenchmarkType, EvaluationMode
from ..services.base import BaseModelService
from ..services.scoring import compare_outputs, compare_text_outputs


# Mode configurations
QUICK_CONFIGS = [
    {"key": "precise", "name": "Precise (temp=0)", "temperature": 0.0, "top_p": 1.0, "max_tokens": 2048}
]

STANDARD_CONFIGS = [
    {"key": "precise", "name": "Precise (temp=0)", "temperature": 0.0, "top_p": 1.0, "max_tokens": 2048},
    {"key": "balanced", "name": "Balanced (temp=0.5)", "temperature": 0.5, "top_p": 1.0, "max_tokens": 2048},
    {"key": "creative", "name": "Creative (temp=1.0)", "temperature": 1.0, "top_p": 1.0, "max_tokens": 2048},
]

DEFAULT_SWEEP_CONFIGS = [
    {"key": "temp_0.0", "name": "Temperature=0.0", "temperature": 0.0, "top_p": 1.0, "max_tokens": 2048},
    {"key": "temp_0.3", "name": "Temperature=0.3", "temperature": 0.3, "top_p": 1.0, "max_tokens": 2048},
    {"key": "temp_0.5", "name": "Temperature=0.5", "temperature": 0.5, "top_p": 1.0, "max_tokens": 2048},
    {"key": "temp_0.7", "name": "Temperature=0.7", "temperature": 0.7, "top_p": 1.0, "max_tokens": 2048},
    {"key": "temp_1.0", "name": "Temperature=1.0", "temperature": 1.0, "top_p": 1.0, "max_tokens": 2048},
]

SWEEPABLE_PARAMETERS = {
    "temperature": {"name": "Temperature", "type": "float", "min": 0.0, "max": 2.0, "step": 0.1},
    "top_p": {"name": "Top P", "type": "float", "min": 0.0, "max": 1.0, "step": 0.05},
    "max_tokens": {"name": "Max Tokens", "type": "int", "min": 256, "max": 8192, "step": 256},
}

SWEEP_TOP_N_MODELS = 3


def get_mode_configs(mode: BenchmarkMode) -> List[Dict]:
    """Get configuration list for a given mode."""
    if mode == BenchmarkMode.QUICK:
        return QUICK_CONFIGS
    elif mode == BenchmarkMode.STANDARD:
        return STANDARD_CONFIGS
    elif mode == BenchmarkMode.SWEEP:
        return DEFAULT_SWEEP_CONFIGS
    return QUICK_CONFIGS


def generate_sweep_configs_from_params(sweep_parameters: Dict[str, List[float]]) -> List[Dict]:
    """Generate sweep configurations from user-selected parameters.

    Takes a dict like {"temperature": [0.3, 0.5, 0.7, 1.0], "top_p": [0.9, 1.0]}
    and generates all combinations as config dicts.
    """
    base_config = {
        "temperature": 0.5,
        "top_p": 1.0,
        "max_tokens": 2048,
    }

    param_names = list(sweep_parameters.keys())
    param_values = [sweep_parameters[name] for name in param_names]

    configs = []
    for combo in itertools.product(*param_values):
        config = base_config.copy()
        name_parts = []
        key_parts = []

        for i, param_name in enumerate(param_names):
            value = combo[i]
            config[param_name] = value
            param_label = SWEEPABLE_PARAMETERS.get(param_name, {}).get("name", param_name)
            name_parts.append(f"{param_label}={value}")
            key_parts.append(f"{param_name}_{value}")

        config["name"] = ", ".join(name_parts)
        config["key"] = "_".join(key_parts)
        configs.append(config)

    return configs


def calculate_model_score(results: List[TestResult], model_id: str) -> float:
    """Calculate aggregate score for a model based on its results.

    Uses overall_score if available, falls back to partial_match_pct,
    then exact_match (100 if true, 0 if false).
    """
    model_results = [r for r in results if r.model == model_id and r.success]
    if not model_results:
        return 0.0

    scores = []
    for r in model_results:
        if r.overall_score is not None:
            scores.append(r.overall_score)
        elif r.exact_match is not None:
            scores.append(100.0 if r.exact_match else 0.0)
        else:
            scores.append(50.0)

    return sum(scores) / len(scores) if scores else 0.0


async def run_single_test(
    test: TestCase,
    model_id: str,
    config: Dict,
    prompt: str,
    output_schema: Optional[Dict],
    service: BaseModelService,
    benchmark_type: BenchmarkType = BenchmarkType.SCHEMATIZED,
    progress_callback: Optional[Callable] = None,
) -> TestResult:
    """Run a single test against a single model with a single config.

    Args:
        test: Test case to run
        model_id: Model identifier
        config: Parameter configuration (temp, top_p, max_tokens, etc.)
        prompt: Task prompt
        output_schema: Output JSON schema (for schematized benchmarks)
        service: Model service instance
        benchmark_type: Type of benchmark (schematized or unschematized)
        progress_callback: Optional callback for progress updates

    Returns:
        TestResult object with execution results
    """
    has_document = bool(test.file_path)
    has_text = bool(test.input_text and test.input_text.strip())
    is_unschematized = benchmark_type == BenchmarkType.UNSCHEMATIZED

    expected_text = None
    if is_unschematized and test.expected_output:
        if isinstance(test.expected_output, str):
            expected_text = test.expected_output
        elif isinstance(test.expected_output, dict):
            expected_text = test.expected_output.get('text', str(test.expected_output))
        else:
            expected_text = str(test.expected_output)


    try:
        if is_unschematized:
            if has_document:
                with open(test.file_path, 'rb') as f:
                    file_data = f.read()

                file_type = test.file_type or _get_mime_type(test.file_path)

                messages = [{"role": "user", "content": prompt}]

                result_dict = service.call_model_with_document(
                    model=model_id,
                    messages=messages,
                    file_data=file_data,
                    file_type=file_type,
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                )

                output_text = result_dict.get("output_text", "")

                if expected_text and result_dict.get("success"):
                    score_result = compare_text_outputs(output_text, expected_text)
                else:
                    score_result = {
                        "exact_match": False,
                        "overall_score": 0.0,
                        "attribute_scores": {},
                        "attribute_matches": {},
                    }

                result = {
                    "success": result_dict.get("success", False),
                    "output_text": output_text,
                    "output": None,
                    "input_tokens": result_dict.get("input_tokens"),
                    "output_tokens": result_dict.get("output_tokens"),
                    "latency_ms": result_dict.get("latency_ms"),
                    "stop_reason": result_dict.get("stop_reason"),
                    "error": result_dict.get("error"),
                    **score_result,
                }

            elif has_text:
                full_prompt = f"{prompt}\n\nInput:\n{test.input_text}"
                messages = [{"role": "user", "content": full_prompt}]

                result_dict = service.call_model(
                    model=model_id,
                    messages=messages,
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                )

                output_text = result_dict.get("output_text", "")

                if expected_text and result_dict.get("success"):
                    score_result = compare_text_outputs(output_text, expected_text)
                else:
                    score_result = {
                        "exact_match": False,
                        "overall_score": 0.0,
                        "attribute_scores": {},
                        "attribute_matches": {},
                    }

                result = {
                    "success": result_dict.get("success", False),
                    "output_text": output_text,
                    "output": None,
                    "input_tokens": result_dict.get("input_tokens"),
                    "output_tokens": result_dict.get("output_tokens"),
                    "latency_ms": result_dict.get("latency_ms"),
                    "stop_reason": result_dict.get("stop_reason"),
                    "error": result_dict.get("error"),
                    **score_result,
                }
            else:
                result = {
                    "success": False,
                    "error": "Test has no input (neither text nor document)",
                    "output": None,
                    "output_text": None,
                }
        else:
            if has_document:
                with open(test.file_path, 'rb') as f:
                    file_data = f.read()

                file_type = test.file_type or _get_mime_type(test.file_path)

                messages = [{"role": "user", "content": prompt}]
                if has_text:
                    messages[0]["content"] = f"{prompt}\n\nAdditional context:\n{test.input_text}"

                result_dict = service.call_model_with_document(
                    model=model_id,
                    messages=messages,
                    file_data=file_data,
                    file_type=file_type,
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                    output_schema=output_schema,
                )

                output = result_dict.get("output_json")

                if test.expected_output and result_dict.get("success") and output:
                    score_result = compare_outputs(output, test.expected_output)
                else:
                    score_result = {
                        "exact_match": False,
                        "overall_score": 0.0,
                        "attribute_scores": {},
                        "attribute_matches": {},
                    }

                result = {
                    "success": result_dict.get("success", False),
                    "output": output,
                    "output_text": None,
                    "input_tokens": result_dict.get("input_tokens"),
                    "output_tokens": result_dict.get("output_tokens"),
                    "latency_ms": result_dict.get("latency_ms"),
                    "stop_reason": result_dict.get("stop_reason"),
                    "error": result_dict.get("error"),
                    **score_result,
                }

            elif has_text:
                full_prompt = f"{prompt}\n\nInput:\n{test.input_text}"
                messages = [{"role": "user", "content": full_prompt}]

                result_dict = service.call_model(
                    model=model_id,
                    messages=messages,
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                    output_schema=output_schema,
                )

                output = result_dict.get("output_json")

                if test.expected_output and result_dict.get("success") and output:
                    score_result = compare_outputs(output, test.expected_output)
                else:
                    score_result = {
                        "exact_match": False,
                        "overall_score": 0.0,
                        "attribute_scores": {},
                        "attribute_matches": {},
                    }

                result = {
                    "success": result_dict.get("success", False),
                    "output": output,
                    "output_text": None,
                    "input_tokens": result_dict.get("input_tokens"),
                    "output_tokens": result_dict.get("output_tokens"),
                    "latency_ms": result_dict.get("latency_ms"),
                    "stop_reason": result_dict.get("stop_reason"),
                    "error": result_dict.get("error"),
                    **score_result,
                }
            else:
                result = {
                    "success": False,
                    "error": "Test has no input (neither text nor document)",
                    "output": None,
                    "output_text": None,
                }

        total_tokens = (result.get("input_tokens") or 0) + (result.get("output_tokens") or 0)
        tokens_per_second = None
        if result.get("latency_ms") and total_tokens:
            tokens_per_second = round((total_tokens / result["latency_ms"]) * 1000, 2)

        from ..utils.pricing import calculate_cost
        input_tokens = result.get("input_tokens") or 0
        output_tokens = result.get("output_tokens") or 0
        estimated_cost = calculate_cost(model_id, input_tokens, output_tokens) if (input_tokens or output_tokens) else None

        test_result = TestResult(
            test_name=test.name,
            model=model_id,
            preset=config["key"],
            preset_name=config["name"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            max_tokens=config["max_tokens"],
            success=result.get("success", False),
            input_text=test.input_text,
            file_name=test.file_path.split('/')[-1] if test.file_path else None,
            prompt=prompt,
            expected_output=test.expected_output,
            output=result.get("output"),
            output_text=result.get("output_text"),
            input_tokens=result.get("input_tokens"),
            output_tokens=result.get("output_tokens"),
            latency_ms=result.get("latency_ms"),
            stop_reason=result.get("stop_reason"),
            exact_match=result.get("exact_match"),
            overall_score=result.get("overall_score"),
            attribute_scores=result.get("attribute_scores"),
            attribute_matches=result.get("attribute_matches"),
            error=result.get("error"),
            total_tokens=total_tokens if total_tokens > 0 else None,
            tokens_per_second=tokens_per_second,
            estimated_cost=estimated_cost,
        )

        if progress_callback:
            progress_callback(test_result)

        return test_result

    except Exception as e:
        error_result = TestResult(
            test_name=test.name,
            model=model_id,
            preset=config["key"],
            preset_name=config["name"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            max_tokens=config["max_tokens"],
            success=False,
            input_text=test.input_text,
            file_name=test.file_path.split('/')[-1] if test.file_path else None,
            prompt=prompt,
            expected_output=test.expected_output,
            output=None,
            error=str(e),
        )

        if progress_callback:
            progress_callback(error_result)

        return error_result


def _get_mime_type(file_path: str) -> str:
    """Determine MIME type from file extension."""
    ext = file_path.lower().split('.')[-1]
    mime_map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'csv': 'text/csv',
        'json': 'application/json',
    }
    return mime_map.get(ext, 'application/octet-stream')


async def run_tests_against_models(
    tests: List[TestCase],
    models: List[str],
    mode: BenchmarkMode,
    prompt: str,
    output_schema: Optional[Dict],
    services: Dict[str, BaseModelService],
    benchmark_type: BenchmarkType = BenchmarkType.SCHEMATIZED,
    sweep_parameters: Optional[Dict[str, List[float]]] = None,
    progress_callback: Optional[Callable] = None,
) -> Tuple[List[TestResult], Optional[Dict]]:
    """Run all tests against all models with parameter configurations based on mode.

    Modes:
    - QUICK: Single temp=0 config for fast model comparison
    - STANDARD: Three temperature configs (0, 0.5, 1.0) for basic parameter variation
    - SWEEP: Automatic two-phase optimization:
        Phase 1: Run all models with temp=0 (like QUICK)
        Phase 2: Sweep top N models with user-selected parameters

    Args:
        tests: List of test cases
        models: List of model IDs to test
        mode: Benchmark mode (QUICK, STANDARD, or SWEEP)
        prompt: Task prompt
        output_schema: Output JSON schema (for schematized benchmarks)
        services: Dict mapping provider name to service instance
        benchmark_type: Type of benchmark (schematized or unschematized)
        sweep_parameters: Dict mapping param name to list of values for SWEEP mode
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (results, sweep_summary) where sweep_summary is None for non-sweep modes
    """
    if mode == BenchmarkMode.SWEEP:
        return await run_sweep_mode(
            tests, models, prompt, output_schema, services,
            benchmark_type, sweep_parameters, progress_callback
        )

    configs = get_mode_configs(mode)

    results = []
    for test in tests:
        for model_id in models:
            provider = _get_model_provider(model_id)
            if provider not in services:
                continue

            service = services[provider]

            for config in configs:
                result = await run_single_test(
                    test, model_id, config, prompt, output_schema,
                    service, benchmark_type, progress_callback
                )
                results.append(result)

    return results, None


async def run_sweep_mode(
    tests: List[TestCase],
    models: List[str],
    prompt: str,
    output_schema: Optional[Dict],
    services: Dict[str, BaseModelService],
    benchmark_type: BenchmarkType = BenchmarkType.SCHEMATIZED,
    sweep_parameters: Optional[Dict[str, List[float]]] = None,
    progress_callback: Optional[Callable] = None,
) -> Tuple[List[TestResult], Dict]:
    """Run automatic two-phase sweep optimization.

    Phase 1: Run all models with temp=0 to identify top performers
    Phase 2: Run parameter sweep on top N models using user-selected parameters

    Args:
        tests: List of test cases
        models: List of model IDs
        prompt: Task prompt
        output_schema: Output JSON schema (for schematized benchmarks)
        services: Dict mapping provider to service instance
        benchmark_type: Type of benchmark
        sweep_parameters: Dict mapping param name to list of values, e.g.
            {"temperature": [0.3, 0.5, 0.7, 1.0], "top_p": [0.9, 1.0]}
            If None, uses default temperature sweep.
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (all_results, sweep_summary)
    """
    all_results = []

    print(f"[SWEEP] Phase 1: Running {len(models)} models with temp=0...")
    phase1_config = QUICK_CONFIGS[0]  # temp=0, deterministic

    for test in tests:
        for model_id in models:
            provider = _get_model_provider(model_id)
            if provider not in services:
                continue

            service = services[provider]

            result = await run_single_test(
                test, model_id, phase1_config, prompt, output_schema,
                service, benchmark_type, progress_callback
            )
            all_results.append(result)

    phase1_count = len(all_results)
    print(f"[SWEEP] Phase 1 complete: {phase1_count} results")

    model_scores = {}
    for model_id in models:
        score = calculate_model_score(all_results, model_id)
        model_scores[model_id] = score
        print(f"[SWEEP] Model {model_id}: score={score:.1f}")

    sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
    top_n = min(SWEEP_TOP_N_MODELS, len(sorted_models))
    top_models = [m[0] for m in sorted_models[:top_n]]
    top_scores = {m[0]: m[1] for m in sorted_models[:top_n]}

    print(f"[SWEEP] Selected top {top_n} models for sweep: {top_models}")

    if sweep_parameters:
        all_sweep_configs = generate_sweep_configs_from_params(sweep_parameters)
        sweep_configs = [c for c in all_sweep_configs if not (
            c.get("temperature") == 0.0 and
            c.get("top_p", 1.0) == 1.0
        )]
        params_desc = ", ".join(f"{k}: {v}" for k, v in sweep_parameters.items())
        print(f"[SWEEP] Using user-selected parameters: {params_desc}")
    else:
        sweep_configs = [c for c in DEFAULT_SWEEP_CONFIGS if c["temperature"] != 0.0]
        print(f"[SWEEP] Using default temperature sweep")

    print(f"[SWEEP] Phase 2: Sweeping {len(sweep_configs)} configs on {len(top_models)} models...")

    for test in tests:
        for model_id in top_models:
            provider = _get_model_provider(model_id)
            if provider not in services:
                continue

            service = services[provider]

            for config in sweep_configs:
                result = await run_single_test(
                    test, model_id, config, prompt, output_schema,
                    service, benchmark_type, progress_callback
                )
                all_results.append(result)

    sweep_count = len(all_results) - phase1_count
    print(f"[SWEEP] Phase 2 complete: {sweep_count} additional results")

    sweep_summary = {
        "phase1_models": models,
        "phase1_results_count": phase1_count,
        "top_models": top_models,
        "top_model_scores": top_scores,
        "sweep_configs_used": [c["name"] for c in sweep_configs],
        "sweep_results_count": sweep_count,
        "selection_criteria": f"Top {top_n} models by overall score from Phase 1 (temp=0)"
    }

    return all_results, sweep_summary


def _get_model_provider(model_id: str) -> str:
    """Determine which provider a model belongs to."""
    from ..services.anthropic import ANTHROPIC_MODELS
    from ..services.google import GOOGLE_MODELS
    from ..services.openai import OPENAI_MODELS
    from ..services.mistral import MISTRAL_MODELS
    from ..services.deepseek import DEEPSEEK_MODELS
    from ..services.groq import GROQ_MODELS

    anthropic_ids = ANTHROPIC_MODELS
    google_ids = GOOGLE_MODELS
    openai_ids = OPENAI_MODELS
    mistral_ids = MISTRAL_MODELS
    deepseek_ids = DEEPSEEK_MODELS
    groq_ids = GROQ_MODELS

    if model_id in anthropic_ids:
        return "anthropic"
    elif model_id in google_ids:
        return "google"
    elif model_id in openai_ids:
        return "openai"
    elif model_id in mistral_ids:
        return "mistral"
    elif model_id in deepseek_ids:
        return "deepseek"
    elif model_id in groq_ids:
        return "groq"
    else:
        raise ValueError(f"Unknown model: {model_id}")


async def run_benchmark(
    config: BenchmarkConfig,
    services: Dict[str, BaseModelService],
    progress_callback: Optional[Callable] = None,
) -> BenchmarkRun:
    """Main entry point: Execute a complete benchmark run.

    Args:
        config: Benchmark configuration with tests, models, mode, etc.
        services: Dict mapping provider name to service instance
            Example: {"anthropic": AnthropicService(...), "openai": OpenAIService(...)}
        progress_callback: Optional callback for progress updates

    Returns:
        BenchmarkRun object with complete results and aggregate stats
    """
    started_at = datetime.utcnow().isoformat()

    results, sweep_summary = await run_tests_against_models(
        tests=config.tests,
        models=config.models,
        mode=config.mode,
        prompt=config.prompt,
        output_schema=config.output_schema,
        services=services,
        benchmark_type=config.benchmark_type,
        sweep_parameters=config.sweep_parameters,
        progress_callback=progress_callback,
    )

    completed_at = datetime.utcnow().isoformat()

    if config.evaluation_mode == EvaluationMode.AI_JUDGE:
        anthropic_key = None
        if "anthropic" in services:
            anthropic_key = services["anthropic"].api_key

        if anthropic_key:
            from ..services.judge import run_judge_evaluation

            results_for_judge = []
            for r in results:
                results_for_judge.append({
                    "model": r.model,
                    "input_text": r.input_text,
                    "file_name": r.file_name,
                    "expected_output": r.expected_output,
                    "output": r.output,
                    "output_text": r.output_text,
                    "success": r.success,
                })

            is_unschematized = config.benchmark_type == BenchmarkType.UNSCHEMATIZED
            judge_results = run_judge_evaluation(
                task_prompt=config.prompt,
                output_schema=config.output_schema,
                results=results_for_judge,
                api_key=anthropic_key,
                is_unschematized=is_unschematized,
            )

            for i, judge_result in enumerate(judge_results):
                if i < len(results):
                    results[i].judge_score = judge_result.get("judge_score")
                    results[i].judge_reasoning = judge_result.get("judge_reasoning")

    from .aggregator import calculate_aggregate_stats
    agg_stats = calculate_aggregate_stats(results)

    run = BenchmarkRun(
        benchmark_config=config,
        mode=config.mode.value,
        models_tested=config.models,
        status="completed",
        results=results,
        total_cost=agg_stats.get("total_cost"),
        avg_latency_ms=agg_stats.get("avg_latency_ms"),
        avg_score=agg_stats.get("avg_score"),
        best_model=agg_stats.get("best_model"),
        fastest_model=agg_stats.get("fastest_model"),
        cheapest_model=agg_stats.get("cheapest_model"),
        started_at=started_at,
        completed_at=completed_at,
    )

    return run
