"""
ModelMouse CLI - Command-line interface for AI model benchmarking.

Provides commands for testing API keys, listing models, getting recommendations,
and running comprehensive benchmarks.
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from modelmouse.core.models import (
    get_all_models,
    get_models_by_provider,
    MODEL_CATALOG,
    get_provider_for_model,
    ModelInfo,
)
from modelmouse.core.types import BenchmarkMode, BenchmarkType, EvaluationMode
from modelmouse.core.schemas import BenchmarkConfig, TestCase
from modelmouse.services.anthropic import AnthropicService
from modelmouse.services.openai import OpenAIService
from modelmouse.services.google import GoogleService
from modelmouse.services.mistral import MistralService
from modelmouse.services.deepseek import DeepSeekService
from modelmouse.services.groq import GroqService
from modelmouse.services.recommendation import get_model_recommendations
from modelmouse.runner.executor import run_benchmark
from modelmouse.runner.progress import LiveBenchmarkDisplay, create_progress_callback
from modelmouse.utils.files import load_json, save_json, save_results
from modelmouse.utils.formatters import (
    format_model_list,
    format_recommendations,
    format_summary,
    format_results_table,
    format_csv,
    format_json,
    format_leaderboard,
    format_detailed_results,
)


app = typer.Typer(
    name="modelmouse",
    help="AI model benchmarking and evaluation CLI",
    add_completion=False,
)
console = Console()


# API Key Management
def get_api_key(cli_key: Optional[str], env_var: str) -> Optional[str]:
    """Get API key from CLI argument or environment variable."""
    if cli_key:
        return cli_key
    return os.getenv(env_var)


def get_all_api_keys(
    anthropic: Optional[str] = None,
    openai: Optional[str] = None,
    google: Optional[str] = None,
    mistral: Optional[str] = None,
    deepseek: Optional[str] = None,
    groq: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Collect all API keys from CLI args or environment."""
    return {
        "anthropic": get_api_key(anthropic, "ANTHROPIC_API_KEY"),
        "openai": get_api_key(openai, "OPENAI_API_KEY"),
        "google": get_api_key(google, "GOOGLE_API_KEY"),
        "mistral": get_api_key(mistral, "MISTRAL_API_KEY"),
        "deepseek": get_api_key(deepseek, "DEEPSEEK_API_KEY"),
        "groq": get_api_key(groq, "GROQ_API_KEY"),
    }


def initialize_services(api_keys: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """Initialize service instances from API keys."""
    services = {}

    if api_keys.get("anthropic"):
        services["anthropic"] = AnthropicService(api_keys["anthropic"])

    if api_keys.get("openai"):
        services["openai"] = OpenAIService(api_keys["openai"])

    if api_keys.get("google"):
        services["google"] = GoogleService(api_keys["google"])

    if api_keys.get("mistral"):
        services["mistral"] = MistralService(api_keys["mistral"])

    if api_keys.get("deepseek"):
        services["deepseek"] = DeepSeekService(api_keys["deepseek"])

    if api_keys.get("groq"):
        services["groq"] = GroqService(api_keys["groq"])

    return services


@app.command()
def test_keys(
    anthropic: Optional[str] = typer.Option(None, "--anthropic", help="Anthropic API key"),
    openai: Optional[str] = typer.Option(None, "--openai", help="OpenAI API key"),
    google: Optional[str] = typer.Option(None, "--google", help="Google API key"),
    mistral: Optional[str] = typer.Option(None, "--mistral", help="Mistral API key"),
    deepseek: Optional[str] = typer.Option(None, "--deepseek", help="DeepSeek API key"),
    groq: Optional[str] = typer.Option(None, "--groq", help="Groq API key"),
):
    """
    Test API connections and display available models.

    Examples:
        modelmouse test-keys --anthropic sk-ant-...
        modelmouse test-keys --anthropic sk-ant-... --openai sk-...
    """
    console.print("\n[bold cyan]Testing API Keys...[/bold cyan]\n")

    api_keys = get_all_api_keys(anthropic, openai, google, mistral, deepseek, groq)

    results_table = Table(title="API Connection Status")
    results_table.add_column("Provider", style="cyan")
    results_table.add_column("Status", justify="center")
    results_table.add_column("Models Available", justify="right")

    any_key_provided = False

    for provider, key in api_keys.items():
        if not key:
            results_table.add_row(
                provider.capitalize(),
                "[dim]Not configured[/dim]",
                "-"
            )
            continue

        any_key_provided = True

        try:
            service = initialize_services({provider: key})[provider]

            models = get_models_by_provider(provider)
            model_count = len(models)

            test_model = models[0] if models else None
            if test_model:
                try:
                    service.call_model(
                        model=test_model,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10,
                        temperature=0.0,
                    )
                    results_table.add_row(
                        provider.capitalize(),
                        "[green]✓ Connected[/green]",
                        str(model_count)
                    )
                except Exception as e:
                    results_table.add_row(
                        provider.capitalize(),
                        f"[yellow]⚠ Key valid but error: {str(e)[:50]}[/yellow]",
                        str(model_count)
                    )
            else:
                results_table.add_row(
                    provider.capitalize(),
                    "[yellow]⚠ No models available[/yellow]",
                    "0"
                )

        except Exception as e:
            results_table.add_row(
                provider.capitalize(),
                f"[red]✗ Failed: {str(e)[:50]}[/red]",
                "-"
            )

    console.print(results_table)

    if not any_key_provided:
        console.print("\n[yellow]No API keys provided. Use --anthropic, --openai, etc. or set environment variables.[/yellow]")
        console.print("Environment variables: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, MISTRAL_API_KEY, DEEPSEEK_API_KEY, GROQ_API_KEY\n")
        raise typer.Exit(1)

    console.print("\n[green]✓ API key testing complete![/green]\n")


@app.command()
def list_models(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Filter by provider (anthropic, openai, google, mistral, deepseek, groq)"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON"
    ),
):
    """
    List available models with their capabilities.

    Examples:
        modelmouse list-models
        modelmouse list-models --provider anthropic
        modelmouse list-models --json
    """
    if provider:
        provider = provider.lower()
        valid_providers = ["anthropic", "openai", "google", "mistral", "deepseek", "groq"]
        if provider not in valid_providers:
            console.print(f"[red]Error: Invalid provider '{provider}'[/red]")
            console.print(f"Valid providers: {', '.join(valid_providers)}")
            raise typer.Exit(1)

        model_ids = get_models_by_provider(provider)
        title = f"{provider.capitalize()} Models"
    else:
        model_ids = get_all_models()
        title = "All Available Models"

    models_info = []
    for model_id in model_ids:
        info = MODEL_CATALOG.get(model_id)
        if info:
            models_info.append({
                "model_id": info.model_id,
                "provider": info.provider,
                "display_name": info.display_name,
                "supports_vision": info.supports_vision,
                "supports_json_schema": info.supports_json_schema,
                "context_window": info.context_window,
                "max_output_tokens": info.max_output_tokens,
            })

    if json_output:
        console.print(format_json(models_info))
    else:
        console.print(f"\n[bold cyan]{title}[/bold cyan]\n")
        console.print(format_model_list(models_info))
        console.print(f"\n[dim]Total: {len(models_info)} models[/dim]\n")


@app.command()
def recommend(
    task: str = typer.Option(..., "--task", help="Task description"),
    schema: Optional[str] = typer.Option(None, "--schema", help="Path to output schema JSON file"),
    tests: Optional[str] = typer.Option(None, "--tests", help="Path to test cases JSON file"),
    anthropic: Optional[str] = typer.Option(None, "--anthropic", help="Anthropic API key (required for recommendations)"),
):
    """
    Get AI-powered model recommendations for a task.

    Examples:
        modelmouse recommend --task "Extract invoice data" --schema schema.json --anthropic sk-ant-...
        modelmouse recommend --task "Summarize articles" --anthropic sk-ant-...
    """
    console.print("\n[bold cyan]Getting Model Recommendations...[/bold cyan]\n")

    api_key = get_api_key(anthropic, "ANTHROPIC_API_KEY")

    if not api_key:
        console.print("[yellow]Warning: No Anthropic API key provided.[/yellow]")
        console.print("Recommendations require an Anthropic API key. Use --anthropic or set ANTHROPIC_API_KEY.\n")
        raise typer.Exit(1)

    output_schema = None
    benchmark_type = "unschematized"
    if schema:
        try:
            output_schema = load_json(schema)
            benchmark_type = "schematized"
            console.print(f"[green]✓ Loaded schema from {schema}[/green]")
        except Exception as e:
            console.print(f"[red]Error loading schema: {e}[/red]")
            raise typer.Exit(1)

    test_cases = []
    if tests:
        try:
            tests_data = load_json(tests)
            if isinstance(tests_data, list):
                test_cases = tests_data
            elif isinstance(tests_data, dict) and "tests" in tests_data:
                test_cases = tests_data["tests"]
            console.print(f"[green]✓ Loaded {len(test_cases)} test cases from {tests}[/green]")
        except Exception as e:
            console.print(f"[red]Error loading tests: {e}[/red]")
            raise typer.Exit(1)

    available_models = []
    for model_id in get_all_models():
        info = MODEL_CATALOG.get(model_id)
        if info:
            available_models.append({
                "id": info.model_id,
                "name": info.display_name,
                "provider": info.provider,
                "context_window": info.context_window,
                "supports_images": info.supports_vision,
                "supports_pdf": info.supports_vision,
                "supports_structured_output": info.supports_json_schema,
                "description": f"{info.display_name} - {info.provider}",
            })

    with console.status("[bold cyan]Analyzing task and generating recommendations...[/bold cyan]"):
        recommendations = get_model_recommendations(
            prompt=task,
            output_schema=output_schema,
            benchmark_type=benchmark_type,
            test_cases=test_cases,
            available_models=available_models,
            api_key=api_key,
        )

    if recommendations.get("recommendations"):
        console.print(format_recommendations(
            recommendations["recommendations"],
            recommendations["overall_reasoning"]
        ))
    else:
        console.print(f"\n[yellow]{recommendations.get('overall_reasoning', 'No recommendations available')}[/yellow]\n")

    console.print("[green]✓ Recommendations complete![/green]\n")


@app.command()
def benchmark(
    task: str = typer.Option(..., "--task", help="Task description/prompt"),
    schema: str = typer.Option(..., "--schema", help="Path to output schema JSON file"),
    tests: str = typer.Option(..., "--tests", help="Path to test cases JSON file"),
    models: List[str] = typer.Option(..., "--models", help="Model IDs to benchmark (can specify multiple)"),
    mode: BenchmarkMode = typer.Option(BenchmarkMode.QUICK, "--mode", help="Benchmark mode (quick/standard/sweep)"),
    sweep_params: Optional[str] = typer.Option(None, "--sweep-params", help="Path to sweep parameters JSON (for sweep mode)"),
    output: Optional[str] = typer.Option(None, "--output", help="Output file path for results"),
    format: str = typer.Option("table", "--format", help="Output format (json/table/csv)"),
    anthropic: Optional[str] = typer.Option(None, "--anthropic", help="Anthropic API key"),
    openai: Optional[str] = typer.Option(None, "--openai", help="OpenAI API key"),
    google: Optional[str] = typer.Option(None, "--google", help="Google API key"),
    mistral: Optional[str] = typer.Option(None, "--mistral", help="Mistral API key"),
    deepseek: Optional[str] = typer.Option(None, "--deepseek", help="DeepSeek API key"),
    groq: Optional[str] = typer.Option(None, "--groq", help="Groq API key"),
):
    """
    Run a comprehensive benchmark across multiple models.

    Examples:
        modelmouse benchmark --task "Extract invoice data" --schema schema.json --tests tests.json --models claude-sonnet-4-5-20250929 --models gpt-4o --anthropic sk-ant-... --openai sk-...

        modelmouse benchmark --task "Extract invoice data" --schema schema.json --tests tests.json --models claude-sonnet-4-5-20250929 --mode sweep --sweep-params sweep.json --output results.json --anthropic sk-ant-...
    """
    console.print("\n[bold cyan]Starting Benchmark...[/bold cyan]\n")

    schema_path = Path(schema)
    tests_path = Path(tests)

    if not schema_path.exists():
        console.print(f"[red]Error: Schema file not found: {schema}[/red]")
        raise typer.Exit(1)

    if not tests_path.exists():
        console.print(f"[red]Error: Tests file not found: {tests}[/red]")
        raise typer.Exit(1)

    try:
        output_schema = load_json(schema)
        console.print(f"[green]✓ Loaded schema from {schema}[/green]")
    except Exception as e:
        console.print(f"[red]Error loading schema: {e}[/red]")
        raise typer.Exit(1)

    try:
        tests_data = load_json(tests)

        test_cases = []
        if isinstance(tests_data, list):
            for test in tests_data:
                test_cases.append(TestCase(**test))
        elif isinstance(tests_data, dict) and "tests" in tests_data:
            for test in tests_data["tests"]:
                test_cases.append(TestCase(**test))
        else:
            console.print(f"[red]Error: Invalid tests file structure[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Loaded {len(test_cases)} test cases from {tests}[/green]")
    except Exception as e:
        console.print(f"[red]Error loading tests: {e}[/red]")
        raise typer.Exit(1)

    sweep_parameters = None
    if sweep_params:
        sweep_params_path = Path(sweep_params)
        if not sweep_params_path.exists():
            console.print(f"[red]Error: Sweep params file not found: {sweep_params}[/red]")
            raise typer.Exit(1)

        try:
            sweep_parameters = load_json(sweep_params)
            console.print(f"[green]✓ Loaded sweep parameters from {sweep_params}[/green]")
        except Exception as e:
            console.print(f"[red]Error loading sweep parameters: {e}[/red]")
            raise typer.Exit(1)

    api_keys = get_all_api_keys(anthropic, openai, google, mistral, deepseek, groq)
    services = initialize_services(api_keys)

    if not services:
        console.print("[red]Error: No API keys provided. At least one API key is required.[/red]")
        console.print("Use --anthropic, --openai, --google, --mistral, --deepseek, or --groq")
        console.print("Or set environment variables: ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.\n")
        raise typer.Exit(1)

    console.print(f"[green]✓ Initialized {len(services)} service(s): {', '.join(services.keys())}[/green]\n")

    models_list = list(models)
    invalid_models = []
    for model in models_list:
        provider = get_provider_for_model(model)
        if not provider:
            console.print(f"[red]Error: Unknown model: {model}[/red]")
            raise typer.Exit(1)

        if provider not in services:
            invalid_models.append((model, provider))

    if invalid_models:
        console.print("[red]Error: Some models cannot be tested due to missing API keys:[/red]")
        for model, provider in invalid_models:
            console.print(f"  - {model} requires {provider} API key")
        console.print()
        raise typer.Exit(1)

    config = BenchmarkConfig(
        name=f"Benchmark: {task[:50]}",
        prompt=task,
        output_schema=output_schema,
        benchmark_type=BenchmarkType.SCHEMATIZED,
        mode=mode,
        evaluation_mode=EvaluationMode.SCHEMA_MATCH,
        tests=test_cases,
        models=models_list,
        sweep_parameters=sweep_parameters,
    )

    if mode == BenchmarkMode.QUICK:
        configs_per_model = 1
    elif mode == BenchmarkMode.STANDARD:
        configs_per_model = 3
    elif mode == BenchmarkMode.SWEEP:
        configs_per_model = 1 + (3 * 5) / len(models_list)
    else:
        configs_per_model = 1

    total_tests = len(test_cases) * len(models_list) * configs_per_model

    display = LiveBenchmarkDisplay(
        total_tests=int(total_tests),
        models=models_list,
        console=console,
    )
    progress_callback = create_progress_callback(display)

    console.print(f"[bold cyan]Running benchmark in {mode.value} mode...[/bold cyan]\n")
    display.start()

    try:
        loop = asyncio.get_event_loop()
        benchmark_run = loop.run_until_complete(
            run_benchmark(config, services, progress_callback)
        )
    except KeyboardInterrupt:
        display.stop()
        console.print("\n[yellow]Benchmark interrupted by user[/yellow]\n")
        raise typer.Exit(130)
    except Exception as e:
        display.stop()
        console.print(f"\n[red]Error running benchmark: {e}[/red]\n")
        raise typer.Exit(1)

    display.stop()
    display.print_final_summary()

    if output:
        try:
            results_dict = benchmark_run.model_dump()
            save_json(results_dict, output)
            console.print(f"\n[green]✓ Results saved to {output}[/green]")
        except Exception as e:
            console.print(f"\n[yellow]Warning: Could not save results: {e}[/yellow]")

    console.print(f"\n[bold cyan]Results ({format} format):[/bold cyan]\n")

    if format == "json":
        results_json = benchmark_run.model_dump()
        console.print(format_json(results_json))

    elif format == "table":
        results_data = [r.model_dump() for r in benchmark_run.results]
        benchmark_type = "schematized" if config.output_schema else "unschematized"

        console.print(format_leaderboard(results_data, benchmark_type=benchmark_type))

        if len(test_cases) > 1 or len(models_list) > 1:
            console.print(format_detailed_results(results_data, group_by="model"))

    elif format == "csv":
        results_data = [r.model_dump() for r in benchmark_run.results]
        headers = ["model", "test_name", "overall_score", "latency_ms", "estimated_cost", "success"]
        csv_output = format_csv(results_data, headers)
        console.print(csv_output)

    else:
        console.print(f"[yellow]Warning: Unknown format '{format}', using table[/yellow]")
        results_data = [r.model_dump() for r in benchmark_run.results]
        console.print(format_results_table(results_data))

    console.print("\n[green]✓ Benchmark complete![/green]\n")


@app.command()
def test_invoice(
    anthropic: Optional[str] = typer.Option(None, "--anthropic", help="Anthropic API key"),
    openai: Optional[str] = typer.Option(None, "--openai", help="OpenAI API key"),
    google: Optional[str] = typer.Option(None, "--google", help="Google API key"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """
    Quick test: Run invoice extraction benchmark with included PDFs.

    Tests vision models on extracting structured data from 3 sample invoices.
    Uses the bundled example files - no setup required!

    Example:
        modelmouse test-invoice --anthropic sk-ant-... --openai sk-...
    """
    console.print("\n[bold cyan]🧪 Invoice Extraction Test[/bold cyan]\n")
    console.print("Testing vision models on PDF invoice extraction...")
    console.print("Using 3 sample invoices from examples/\n")

    package_root = Path(__file__).parent.parent
    examples_dir = package_root / "examples" / "invoice_extraction"

    schema_file = examples_dir / "schema.json"
    tests_file = examples_dir / "tests.json"

    if not schema_file.exists() or not tests_file.exists():
        console.print(f"[red]Error: Example files not found at {examples_dir}[/red]")
        console.print("[yellow]Make sure you're running from the installed package.[/yellow]")
        raise typer.Exit(1)

    try:
        schema = load_json(str(schema_file))
        tests_data = load_json(str(tests_file))
    except Exception as e:
        console.print(f"[red]Error loading example files: {e}[/red]")
        raise typer.Exit(1)

    test_cases = []
    for test_data in tests_data:
        if test_data.get("file_path"):
            test_data["file_path"] = str(package_root / test_data["file_path"])
        test_cases.append(TestCase(**test_data))

    config = BenchmarkConfig(
        name="Invoice Extraction Test",
        prompt="Extract the invoice details including invoice number, date, vendor, total, and line items if present.",
        output_schema=schema,
        tests=test_cases,
        models=["claude-sonnet-4-5-20250929", "gpt-4o", "gemini-2.5-flash"],
        mode=BenchmarkMode.QUICK,
        benchmark_type=BenchmarkType.SCHEMATIZED,
        evaluation_mode=EvaluationMode.SCHEMA_MATCH,
    )

    api_keys = get_all_api_keys(anthropic=anthropic, openai=openai, google=google)

    services = {}
    if api_keys.get("anthropic"):
        services["anthropic"] = AnthropicService(api_keys["anthropic"])
    if api_keys.get("openai"):
        services["openai"] = OpenAIService(api_keys["openai"])
    if api_keys.get("google"):
        services["google"] = GoogleService(api_keys["google"])

    if not services:
        console.print("[red]Error: At least one API key required[/red]")
        console.print("Provide --anthropic, --openai, or --google")
        raise typer.Exit(1)

    available_models = []
    for model in config.models:
        provider = get_provider_for_model(model)
        if provider in services:
            available_models.append(model)

    if not available_models:
        console.print("[red]Error: No models available with provided API keys[/red]")
        console.print(f"Required providers: anthropic, openai, google")
        raise typer.Exit(1)

    config.models = available_models
    console.print(f"[green]Testing models: {', '.join(available_models)}[/green]\n")

    display = LiveBenchmarkDisplay(
        total_tests=len(config.tests) * len(config.models),
        models=config.models
    )
    display.start()

    benchmark_run = asyncio.run(run_benchmark(config, services, display.update))

    display.stop()
    display.print_final_summary()

    if output:
        output_path = output
    else:
        output_path = save_results(benchmark_run.model_dump())

    console.print(f"\n[green]✓ Results saved to: {output_path}[/green]")

    results_dicts = [r.model_dump() for r in benchmark_run.results]
    benchmark_type = "schematized" if config.output_schema else "unschematized"

    console.print(format_leaderboard(results_dicts, benchmark_type=benchmark_type))

    console.print("\n[green]✓ Test complete![/green]\n")


@app.command()
def test_sentiment(
    anthropic: Optional[str] = typer.Option(None, "--anthropic", help="Anthropic API key"),
    openai: Optional[str] = typer.Option(None, "--openai", help="OpenAI API key"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """
    Quick test: Run sentiment analysis benchmark with sample reviews.

    Tests models on free-form text analysis with AI Judge evaluation.
    Uses the bundled example files - no setup required!

    Example:
        modelmouse test-sentiment --anthropic sk-ant-... --openai sk-...
    """
    console.print("\n[bold cyan]🧪 Sentiment Analysis Test[/bold cyan]\n")
    console.print("Testing models on sentiment analysis (unschematized)...")
    console.print("Using 4 sample reviews from examples/")
    console.print("[yellow]AI Judge evaluation enabled automatically[/yellow]\n")

    package_root = Path(__file__).parent.parent
    examples_dir = package_root / "examples" / "sentiment_analysis"

    tests_file = examples_dir / "tests.json"

    if not tests_file.exists():
        console.print(f"[red]Error: Example files not found at {examples_dir}[/red]")
        console.print("[yellow]Make sure you're running from the installed package.[/yellow]")
        raise typer.Exit(1)

    try:
        tests_data = load_json(str(tests_file))
    except Exception as e:
        console.print(f"[red]Error loading example files: {e}[/red]")
        raise typer.Exit(1)

    test_cases = [TestCase(**test_data) for test_data in tests_data]

    config = BenchmarkConfig(
        name="Sentiment Analysis Test",
        prompt="Analyze the sentiment of the following review. Explain the overall sentiment (positive, negative, neutral, or mixed), the tone, and key factors that contribute to this sentiment.",
        output_schema=None,
        tests=test_cases,
        models=["claude-haiku-4-5-20251001", "gpt-4o-mini"],
        mode=BenchmarkMode.QUICK,
        benchmark_type=BenchmarkType.UNSCHEMATIZED,
        evaluation_mode=EvaluationMode.AI_JUDGE,
    )

    api_keys = get_all_api_keys(anthropic=anthropic, openai=openai)

    services = {}
    if api_keys.get("anthropic"):
        services["anthropic"] = AnthropicService(api_keys["anthropic"])
    if api_keys.get("openai"):
        services["openai"] = OpenAIService(api_keys["openai"])

    if not services:
        console.print("[red]Error: At least one API key required[/red]")
        console.print("Provide --anthropic or --openai")
        raise typer.Exit(1)

    available_models = []
    for model in config.models:
        provider = get_provider_for_model(model)
        if provider in services:
            available_models.append(model)

    if not available_models:
        console.print("[red]Error: No models available with provided API keys[/red]")
        console.print(f"Required providers: anthropic, openai")
        raise typer.Exit(1)

    config.models = available_models
    console.print(f"[green]Testing models: {', '.join(available_models)}[/green]\n")

    display = LiveBenchmarkDisplay(
        total_tests=len(config.tests) * len(config.models),
        models=config.models
    )
    display.start()

    benchmark_run = asyncio.run(run_benchmark(config, services, display.update))

    display.stop()
    display.print_final_summary()

    if output:
        output_path = output
    else:
        output_path = save_results(benchmark_run.model_dump())

    console.print(f"\n[green]✓ Results saved to: {output_path}[/green]")

    results_dicts = [r.model_dump() for r in benchmark_run.results]
    benchmark_type = "unschematized" if config.evaluation_mode == EvaluationMode.AI_JUDGE else "schematized"

    console.print(format_leaderboard(results_dicts, benchmark_type=benchmark_type))

    console.print("\n[green]✓ Test complete![/green]\n")


@app.command()
def version():
    """Display version information."""
    console.print("\n[bold cyan]ModelMouse CLI[/bold cyan]")
    console.print("Version: 0.1.0")
    console.print("AI Model Benchmarking and Evaluation Tool\n")


if __name__ == "__main__":
    app()
