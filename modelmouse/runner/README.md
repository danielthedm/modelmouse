# Benchmark Runner Modules

Standalone benchmark orchestration logic extracted from the Modelator backend for use in the modelmouse CLI tool.

## Overview

These modules provide sophisticated benchmark execution capabilities without database dependencies:

- **executor.py** - Core benchmark execution logic with sweep mode support
- **aggregator.py** - Result aggregation and statistical analysis
- **progress.py** - Rich CLI progress display and status tracking

## Features

### Execution Modes

1. **Quick Mode**: Single deterministic config (temp=0) for fast model comparison
2. **Standard Mode**: Three temperature configs (0, 0.5, 1.0) for basic parameter variation
3. **Sweep Mode**: Two-phase automatic optimization
   - Phase 1: Test all models with temp=0
   - Phase 2: Parameter sweep on top N models

### Key Capabilities

- ✅ Schematized benchmarks (JSON schema validation)
- ✅ Unschematized benchmarks (free-form text evaluation)
- ✅ Document/image inputs (PDF, images, etc.)
- ✅ Text inputs
- ✅ Retry logic with exponential backoff
- ✅ Token counting and latency tracking
- ✅ Cost estimation
- ✅ Real-time progress display
- ✅ Aggregate statistics (best/fastest/cheapest model)

## Usage

### Basic Example

```python
import asyncio
from modelmouse.core.schemas import BenchmarkConfig, TestCase
from modelmouse.core.types import BenchmarkMode, BenchmarkType
from modelmouse.services.anthropic import AnthropicService
from modelmouse.runner import run_benchmark

async def main():
    # Configure benchmark
    config = BenchmarkConfig(
        prompt="Extract invoice details",
        output_schema={
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string"},
                "total": {"type": "number"},
            }
        },
        tests=[
            TestCase(
                name="Invoice 1",
                input_text="Invoice #12345, Total: $100.00",
                expected_output={
                    "invoice_number": "12345",
                    "total": 100.0
                }
            )
        ],
        models=["claude-3-haiku-20240307"],
        mode=BenchmarkMode.QUICK,
    )

    # Initialize services
    services = {
        "anthropic": AnthropicService(api_key="sk-..."),
    }

    # Run benchmark
    result = await run_benchmark(config, services)

    print(f"Best model: {result.best_model}")
    print(f"Average score: {result.avg_score}")
    print(f"Total cost: ${result.total_cost}")

asyncio.run(main())
```

### With Progress Display

```python
from modelmouse.runner import LiveBenchmarkDisplay, create_progress_callback

# Set up progress display
total_tests = len(config.tests) * len(config.models)
display = LiveBenchmarkDisplay(total_tests, config.models)
progress_callback = create_progress_callback(display)

# Run with progress
display.start()
try:
    result = await run_benchmark(config, services, progress_callback)
finally:
    display.stop()

display.print_final_summary()
```

### Sweep Mode

```python
config = BenchmarkConfig(
    # ... other config ...
    mode=BenchmarkMode.SWEEP,
    sweep_parameters={
        "temperature": [0.3, 0.5, 0.7, 1.0],
        "top_p": [0.9, 1.0],
    }
)

result = await run_benchmark(config, services)
```

### Document/Image Benchmarks

```python
config = BenchmarkConfig(
    prompt="Extract data from this invoice image",
    output_schema={...},
    tests=[
        TestCase(
            name="Invoice Image 1",
            file_path="/path/to/invoice.pdf",
            file_type="application/pdf",
            expected_output={...}
        )
    ],
    models=["claude-3-haiku-20240307"],
)
```

## Module Reference

### executor.py

Main execution functions:

- `run_benchmark(config, services, progress_callback)` - Main entry point
- `run_tests_against_models(...)` - Execute tests with mode-based configs
- `run_single_test(...)` - Execute a single test against a single model
- `run_sweep_mode(...)` - Two-phase sweep optimization

### aggregator.py

Statistics and analysis functions:

- `calculate_aggregate_stats(results)` - Overall run statistics
- `calculate_per_model_stats(results)` - Per-model breakdown
- `calculate_per_test_stats(results)` - Per-test breakdown
- `rank_models_by_metric(results, metric)` - Rank models by score/latency/cost
- `format_summary_report(results)` - Generate text summary

### progress.py

Progress display classes:

- `BenchmarkProgress` - Simple progress bar tracker
- `LiveBenchmarkDisplay` - Real-time updating display with results table
- `create_progress_callback(display)` - Create callback function for executor

## Architecture Notes

### No Database Dependencies

These modules operate entirely in memory:

- Results returned as Pydantic models (`BenchmarkRun`, `TestResult`)
- No SQLAlchemy, no database connections
- Services initialized with API keys directly
- Results can be serialized to JSON for persistence

### Service Integration

The runner expects a dict mapping provider names to service instances:

```python
services = {
    "anthropic": AnthropicService(api_key="..."),
    "openai": OpenAIService(api_key="..."),
    "google": GoogleService(api_key="..."),
}
```

Services must implement the `BaseModelService` interface:
- `call_model(model, messages, max_tokens, temperature, output_schema)`
- `call_model_with_document(model, messages, file_data, file_type, ...)`

### Retry Logic

Built-in retry with exponential backoff for rate limits:
- Max 3 retries
- Initial backoff: 2 seconds
- Max backoff: 30 seconds
- Random jitter to prevent thundering herd

### Cost Calculation

Uses pricing data from `modelmouse.utils.pricing`:
- Token counts from service responses
- Model-specific pricing per 1K tokens
- Aggregated across all tests

## Sweep Mode Details

Sweep mode provides automatic parameter optimization:

**Phase 1: Quick Evaluation**
- Runs all models with temp=0 (deterministic)
- Calculates scores for each model
- Ranks models by average score

**Phase 2: Parameter Sweep**
- Selects top N models (default: 3)
- Tests each with user-defined parameter combinations
- Generates all combinations from sweep_parameters dict

Example sweep with temperature and top_p:
```python
sweep_parameters = {
    "temperature": [0.3, 0.5, 0.7, 1.0],  # 4 values
    "top_p": [0.9, 1.0],                   # 2 values
}
# Creates 4 × 2 = 8 configurations per top model
```

## Error Handling

The executor handles various error cases:

- Service API errors (returned in TestResult.error)
- File read errors for documents
- JSON parsing errors for structured output
- Rate limits (automatic retry)
- Missing or invalid test inputs

All errors are captured and returned in results rather than raising exceptions.

## Performance Considerations

**Execution Time**:
- Quick mode: ~1-2 seconds per test per model
- Standard mode: ~3-6 seconds per test per model (3 configs)
- Sweep mode: Phase 1 + (top_n_models × sweep_configs × tests)

**Cost Estimation**:
- Displayed in real-time during execution
- Aggregated in final results
- Based on actual token counts from service responses

**Memory Usage**:
- Results stored in memory during execution
- Minimal overhead - just Pydantic models
- Can handle 1000s of tests without issues

## Example CLI Integration

See `examples/benchmark_example.py` for a complete working example.

For CLI integration, you can:
1. Parse arguments to build BenchmarkConfig
2. Load API keys from environment or config file
3. Initialize services with API keys
4. Run benchmark with progress display
5. Save results to JSON file
6. Display summary table

## Differences from Backend

Changes made for CLI standalone usage:

- ❌ No database operations (removed all SQLAlchemy code)
- ❌ No FastAPI dependencies (removed BackgroundTasks)
- ❌ No user/tier checks (removed authentication)
- ✅ Synchronous service initialization
- ✅ Direct API key passing (no database lookup)
- ✅ In-memory results (no persistence)
- ✅ Progress callbacks instead of DB status updates
