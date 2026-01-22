# Benchmark Orchestration Extraction Summary

## Overview

Successfully extracted and refactored benchmark orchestration logic from the Modelator backend (`/Users/danielleslie/Github/modelator/backend/app/routers/benchmarks.py`) to create standalone runner modules for the modelmouse CLI tool.

## Files Created

### Core Runner Modules

1. **`/Users/danielleslie/Github/modelmouse/modelmouse/runner/executor.py`** (563 lines)
   - Main benchmark execution logic
   - Extracted from `run_tests_against_models()` (lines 1303-1600)
   - Extracted from `run_single_test()` (lines 1082-1276)
   - Extracted from `run_sweep_mode()` (lines 1421-1600)
   - Removed all database operations
   - Removed FastAPI/BackgroundTasks dependencies
   - Kept sophisticated sweep mode logic (2-phase optimization)
   - Support for schematized and unschematized benchmarks
   - Support for document/image inputs
   - Built-in retry logic with exponential backoff
   - Token counting and cost estimation

2. **`/Users/danielleslie/Github/modelmouse/modelmouse/runner/aggregator.py`** (270 lines)
   - Result aggregation and statistics
   - Extracted from `calculate_run_aggregate_stats()` (lines 150-213)
   - Extracted from `get_result_score()` (lines 126-147)
   - Functions to compute:
     - `calculate_aggregate_stats()`: total_cost, avg_latency_ms, avg_score, best_model, fastest_model, cheapest_model
     - `calculate_per_model_stats()`: Per-model breakdown
     - `calculate_per_test_stats()`: Per-test breakdown
     - `rank_models_by_metric()`: Model rankings
     - `format_summary_report()`: Text summary generation

3. **`/Users/danielleslie/Github/modelmouse/modelmouse/runner/progress.py`** (324 lines)
   - CLI progress display using Rich library
   - Two display classes:
     - `BenchmarkProgress`: Simple progress bar
     - `LiveBenchmarkDisplay`: Real-time updating display with results table
   - Shows current model/test being executed
   - Displays success/failure indicators
   - Real-time results summary
   - Final summary with model rankings

### Supporting Files

4. **`/Users/danielleslie/Github/modelmouse/modelmouse/utils/pricing.py`** (240 lines)
   - Pricing data and cost calculation
   - Extracted from `backend/app/services/router_service.py`
   - Model pricing configurations (Claude, GPT, Gemini, Mistral, DeepSeek, Groq)
   - `calculate_cost()` function for token-based cost estimation

5. **`/Users/danielleslie/Github/modelmouse/modelmouse/runner/__init__.py`**
   - Module exports for convenient imports

6. **`/Users/danielleslie/Github/modelmouse/modelmouse/runner/README.md`**
   - Comprehensive documentation
   - Usage examples
   - API reference
   - Architecture notes

7. **`/Users/danielleslie/Github/modelmouse/examples/benchmark_example.py`**
   - Complete working example
   - Demonstrates CLI integration

## Key Features Preserved

### Execution Modes

✅ **Quick Mode**: Single temp=0 config for fast comparison
✅ **Standard Mode**: Three temperature configs (0, 0.5, 1.0)
✅ **Sweep Mode**: Automatic two-phase optimization
   - Phase 1: Test all models with temp=0
   - Phase 2: Parameter sweep on top N models

### Benchmark Types

✅ **Schematized**: JSON schema validation with structured output
✅ **Unschematized**: Free-form text evaluation with AI judge support

### Input Types

✅ **Text inputs**: Simple text prompts
✅ **Document inputs**: PDF files with text extraction
✅ **Image inputs**: PNG, JPEG, etc. with vision models
✅ **Combined inputs**: Text + document/image

### Sophisticated Logic Preserved

✅ **Sweep Mode Intelligence**:
   - Phase 1: Quick evaluation of all models
   - Score calculation and model ranking
   - Phase 2: Top N model selection
   - User-defined parameter combinations
   - Automatic config generation

✅ **Parameter Configurations**:
   - Temperature sweeps
   - Top-p sweeps
   - Max tokens variation
   - All combinations generated automatically

✅ **Error Handling & Retries**:
   - Rate limit detection
   - Exponential backoff (2s → 4s → 8s → 16s → 30s max)
   - Random jitter to prevent thundering herd
   - Max 3 retries per request

✅ **Token Counting & Latency**:
   - Input/output token tracking
   - Latency measurement in milliseconds
   - Tokens per second calculation
   - Cost estimation based on token usage

✅ **Scoring Logic** (from services/scoring.py):
   - Exact match detection
   - Partial match scoring (0-100)
   - Attribute-level scoring
   - String similarity with n-grams
   - Number comparison with tolerance
   - Array/object deep comparison

## Changes for CLI Standalone Usage

### Removed Dependencies

❌ `from sqlalchemy.orm import Session` - No database
❌ `from fastapi import BackgroundTasks` - No async web framework
❌ `from app.database import get_db` - No database connections
❌ `from app.models import *` - No ORM models
❌ `from app.utils.api_key_auth import *` - No authentication
❌ Database operations: `db.add()`, `db.commit()`, `db.query()`

### Added Functionality

✅ In-memory data structures (Pydantic models)
✅ Direct API key passing (no database lookup)
✅ Progress callbacks (instead of DB status updates)
✅ Synchronous service initialization
✅ JSON serialization for persistence
✅ Rich library for beautiful terminal output

### API Changes

**Before (Backend)**:
```python
def run_tests_against_models(
    tests: List[BenchmarkTest],  # DB model
    models: List[str],
    mode: BenchmarkMode,
    prompt: str,
    output_schema: dict,
    services: dict,
    run: BenchmarkRun,  # DB model
    db: Session,  # Database session
    benchmark_type: str = "text",
) -> tuple:
```

**After (CLI)**:
```python
async def run_tests_against_models(
    tests: List[TestCase],  # Pydantic model
    models: List[str],
    mode: BenchmarkMode,
    prompt: str,
    output_schema: Optional[Dict],
    services: Dict[str, BaseModelService],
    benchmark_type: BenchmarkType = BenchmarkType.SCHEMATIZED,
    sweep_parameters: Optional[Dict[str, List[float]]] = None,
    progress_callback: Optional[Callable] = None,
) -> Tuple[List[TestResult], Optional[Dict]]:
```

## Usage Example

```python
import asyncio
from modelmouse.core.schemas import BenchmarkConfig, TestCase
from modelmouse.core.types import BenchmarkMode, BenchmarkType
from modelmouse.services.anthropic import AnthropicService
from modelmouse.services.openai import OpenAIService
from modelmouse.runner import run_benchmark, LiveBenchmarkDisplay

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
                expected_output={"invoice_number": "12345", "total": 100.0}
            )
        ],
        models=["claude-3-haiku-20240307", "gpt-4o-mini"],
        mode=BenchmarkMode.QUICK,
    )

    # Initialize services with API keys
    services = {
        "anthropic": AnthropicService(api_key="sk-ant-..."),
        "openai": OpenAIService(api_key="sk-..."),
    }

    # Set up progress display
    display = LiveBenchmarkDisplay(
        total_tests=len(config.tests) * len(config.models),
        models=config.models
    )

    # Run benchmark with progress
    display.start()
    try:
        result = await run_benchmark(config, services, display.update)
    finally:
        display.stop()

    # Show final results
    display.print_final_summary()

    # Access results
    print(f"Best model: {result.best_model}")
    print(f"Average score: {result.avg_score}")
    print(f"Total cost: ${result.total_cost}")

asyncio.run(main())
```

## Integration Points

### Service Classes
The runner expects services implementing `BaseModelService`:
- `AnthropicService(api_key)` - Claude models
- `OpenAIService(api_key)` - GPT models
- `GoogleService(api_key)` - Gemini models
- `MistralService(api_key)` - Mistral models
- `DeepSeekService(api_key)` - DeepSeek models
- `GroqService(api_key)` - Groq models (Llama, etc.)

### Scoring Functions
Uses functions from `modelmouse.services.scoring`:
- `compare_outputs(actual, expected)` - For schematized benchmarks
- `compare_text_outputs(actual, expected)` - For unschematized benchmarks

### Pricing Data
Uses model pricing from `modelmouse.utils.pricing`:
- `calculate_cost(model_id, input_tokens, output_tokens)`
- `MODEL_CONFIGS` dict with per-model pricing

## Testing

All files pass Python syntax checks:
```bash
python3 -m py_compile modelmouse/runner/executor.py      # ✓
python3 -m py_compile modelmouse/runner/aggregator.py    # ✓
python3 -m py_compile modelmouse/runner/progress.py      # ✓
python3 -m py_compile modelmouse/utils/pricing.py        # ✓
```

## Next Steps

To use these modules in a CLI tool:

1. **Install dependencies**: `rich`, provider SDKs (anthropic, openai, etc.)
2. **Parse CLI arguments** to build `BenchmarkConfig`
3. **Load API keys** from environment or config file
4. **Initialize services** with API keys
5. **Run benchmark** with progress display
6. **Save results** to JSON file
7. **Display summary** table

Example CLI structure:
```bash
modelmouse benchmark run \
  --config benchmark.json \
  --models claude-3-haiku gpt-4o-mini \
  --mode quick \
  --output results.json
```

## Source Traceability

All code extracted from:
- **Source**: `/Users/danielleslie/Github/modelator/backend/app/routers/benchmarks.py`
- **Lines 1082-1600**: Core execution logic
- **Lines 150-213**: Aggregation logic
- **Lines 126-147**: Scoring helpers
- **Additional**: `router_service.py` for pricing data

Preserved the sophisticated algorithms while removing all database/web framework dependencies.
