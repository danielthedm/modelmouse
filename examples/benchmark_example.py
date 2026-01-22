"""
Example: Running a benchmark with the modelmouse CLI runner.

This demonstrates how to use the standalone benchmark runner modules
without database dependencies.
"""
import asyncio
from modelmouse.core.schemas import BenchmarkConfig, TestCase
from modelmouse.core.types import BenchmarkMode, BenchmarkType, EvaluationMode
from modelmouse.services.anthropic import AnthropicService
from modelmouse.services.openai import OpenAIService
from modelmouse.runner import run_benchmark, LiveBenchmarkDisplay, create_progress_callback


async def main():
    # 1. Define your benchmark configuration
    config = BenchmarkConfig(
        name="Invoice Extraction Test",
        description="Extract structured data from invoices",
        benchmark_type=BenchmarkType.SCHEMATIZED,
        prompt="Extract the invoice details from this document.",
        output_schema={
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string"},
                "date": {"type": "string"},
                "total": {"type": "number"},
                "vendor": {"type": "string"},
            },
            "required": ["invoice_number", "date", "total", "vendor"]
        },
        mode=BenchmarkMode.QUICK,
        evaluation_mode=EvaluationMode.SCHEMA_MATCH,
        tests=[
            TestCase(
                name="Test Invoice 1",
                input_text="Invoice #12345\nDate: 2024-01-15\nVendor: Acme Corp\nTotal: $1,234.56",
                expected_output={
                    "invoice_number": "12345",
                    "date": "2024-01-15",
                    "total": 1234.56,
                    "vendor": "Acme Corp"
                }
            ),
            TestCase(
                name="Test Invoice 2",
                input_text="Invoice #98765\nDate: 2024-02-20\nVendor: Widget Inc\nTotal: $567.89",
                expected_output={
                    "invoice_number": "98765",
                    "date": "2024-02-20",
                    "total": 567.89,
                    "vendor": "Widget Inc"
                }
            ),
        ],
        models=[
            "claude-3-haiku-20240307",
            "gpt-4o-mini",
        ]
    )

    # 2. Initialize service instances with your API keys
    services = {
        "anthropic": AnthropicService(api_key="your-anthropic-key"),
        "openai": OpenAIService(api_key="your-openai-key"),
    }

    # 3. Set up progress display
    total_tests = len(config.tests) * len(config.models)
    display = LiveBenchmarkDisplay(total_tests, config.models)
    progress_callback = create_progress_callback(display)

    # 4. Run the benchmark
    display.start()
    try:
        result = await run_benchmark(
            config=config,
            services=services,
            progress_callback=progress_callback,
        )
    finally:
        display.stop()

    # 5. Display final results
    display.print_final_summary()

    # 6. Access results programmatically
    print(f"\nBest model: {result.best_model}")
    print(f"Average score: {result.avg_score:.2f}")
    print(f"Total cost: ${result.total_cost:.6f}")

    # 7. Export to JSON
    import json
    with open("benchmark_results.json", "w") as f:
        json.dump(result.model_dump(), f, indent=2)

    print("\nResults saved to benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())
