"""
Validation script to test runner module imports and structure.

This verifies that all modules are properly structured and can be imported
without runtime errors (assuming dependencies are installed).
"""

def validate_imports():
    """Test that all runner modules can be imported."""
    print("Testing imports...")

    try:
        # Core schemas
        from modelmouse.core.schemas import BenchmarkConfig, TestCase, TestResult, BenchmarkRun
        from modelmouse.core.types import BenchmarkMode, BenchmarkType, EvaluationMode
        print("✓ Core schemas and types")
    except ImportError as e:
        print(f"✗ Core schemas/types import failed: {e}")
        return False

    try:
        # Runner modules
        from modelmouse.runner import (
            run_benchmark,
            run_single_test,
            run_tests_against_models,
            calculate_aggregate_stats,
            calculate_per_model_stats,
            BenchmarkProgress,
            LiveBenchmarkDisplay,
        )
        print("✓ Runner modules")
    except ImportError as e:
        print(f"✗ Runner import failed: {e}")
        return False

    try:
        # Pricing utilities
        from modelmouse.utils.pricing import calculate_cost, MODEL_CONFIGS
        print("✓ Pricing utilities")
    except ImportError as e:
        print(f"✗ Pricing import failed: {e}")
        return False

    try:
        # Scoring functions
        from modelmouse.services.scoring import compare_outputs, compare_text_outputs
        print("✓ Scoring functions")
    except ImportError as e:
        print(f"✗ Scoring import failed: {e}")
        return False

    print("\n✓ All imports successful!")
    return True


def validate_config_creation():
    """Test that BenchmarkConfig can be created."""
    print("\nTesting config creation...")

    try:
        from modelmouse.core.schemas import BenchmarkConfig, TestCase
        from modelmouse.core.types import BenchmarkMode, BenchmarkType, EvaluationMode

        # Schematized config
        config1 = BenchmarkConfig(
            name="Test Benchmark",
            prompt="Extract data",
            output_schema={
                "type": "object",
                "properties": {"field": {"type": "string"}}
            },
            tests=[
                TestCase(
                    name="Test 1",
                    input_text="Sample input",
                    expected_output={"field": "value"}
                )
            ],
            models=["claude-3-haiku-20240307"],
            mode=BenchmarkMode.QUICK,
            benchmark_type=BenchmarkType.SCHEMATIZED,
        )
        print("✓ Schematized config creation")

        # Unschematized config
        config2 = BenchmarkConfig(
            name="Unschematized Test",
            prompt="Generate a summary",
            output_schema=None,
            tests=[
                TestCase(
                    name="Test 1",
                    input_text="Long text...",
                    expected_output="Summary text"
                )
            ],
            models=["gpt-4o-mini"],
            mode=BenchmarkMode.STANDARD,
            benchmark_type=BenchmarkType.UNSCHEMATIZED,
            evaluation_mode=EvaluationMode.AI_JUDGE,
        )
        print("✓ Unschematized config creation")

        print("\n✓ All configs created successfully!")
        return True

    except Exception as e:
        print(f"✗ Config creation failed: {e}")
        return False


def validate_test_result_structure():
    """Test that TestResult can be created with expected fields."""
    print("\nTesting TestResult structure...")

    try:
        from modelmouse.core.schemas import TestResult

        result = TestResult(
            test_name="Test 1",
            model="claude-3-haiku-20240307",
            preset="precise",
            preset_name="Precise (temp=0)",
            temperature=0.0,
            top_p=1.0,
            max_tokens=2048,
            success=True,
            prompt="Test prompt",
            expected_output={"field": "value"},
            output={"field": "value"},
            input_tokens=100,
            output_tokens=50,
            latency_ms=1234.5,
            stop_reason="end_turn",
            exact_match=True,
            overall_score=100.0,
            estimated_cost=0.001,
        )

        # Verify fields
        assert result.model == "claude-3-haiku-20240307"
        assert result.success is True
        assert result.exact_match is True
        assert result.overall_score == 100.0

        print("✓ TestResult structure valid")
        print(f"  - Model: {result.model}")
        print(f"  - Success: {result.success}")
        print(f"  - Score: {result.overall_score}")
        print(f"  - Cost: ${result.estimated_cost}")

        return True

    except Exception as e:
        print(f"✗ TestResult validation failed: {e}")
        return False


def validate_aggregator():
    """Test aggregator functions with mock data."""
    print("\nTesting aggregator functions...")

    try:
        from modelmouse.core.schemas import TestResult
        from modelmouse.runner.aggregator import (
            calculate_aggregate_stats,
            calculate_per_model_stats,
            format_summary_report,
        )

        # Create mock results
        results = [
            TestResult(
                test_name="Test 1",
                model="model-a",
                preset="precise",
                preset_name="Precise",
                temperature=0.0,
                top_p=1.0,
                max_tokens=2048,
                success=True,
                prompt="Test",
                overall_score=95.0,
                latency_ms=1000.0,
                estimated_cost=0.001,
            ),
            TestResult(
                test_name="Test 1",
                model="model-b",
                preset="precise",
                preset_name="Precise",
                temperature=0.0,
                top_p=1.0,
                max_tokens=2048,
                success=True,
                prompt="Test",
                overall_score=85.0,
                latency_ms=2000.0,
                estimated_cost=0.002,
            ),
        ]

        # Test aggregate stats
        agg_stats = calculate_aggregate_stats(results)
        assert "avg_score" in agg_stats
        assert "total_cost" in agg_stats
        assert "best_model" in agg_stats
        print("✓ Aggregate stats calculation")
        print(f"  - Best model: {agg_stats['best_model']}")
        print(f"  - Avg score: {agg_stats['avg_score']}")
        print(f"  - Total cost: ${agg_stats['total_cost']}")

        # Test per-model stats
        per_model = calculate_per_model_stats(results)
        assert "model-a" in per_model
        assert "model-b" in per_model
        print("✓ Per-model stats calculation")

        # Test summary report
        report = format_summary_report(results)
        assert "BENCHMARK SUMMARY" in report
        assert "model-a" in report
        print("✓ Summary report generation")

        return True

    except Exception as e:
        print(f"✗ Aggregator validation failed: {e}")
        return False


def validate_pricing():
    """Test pricing calculations."""
    print("\nTesting pricing functions...")

    try:
        from modelmouse.utils.pricing import calculate_cost, MODEL_CONFIGS

        # Test cost calculation for known model
        cost = calculate_cost("claude-3-haiku-20240307", 1000, 500)
        assert cost > 0
        print(f"✓ Cost calculation: 1000 input + 500 output = ${cost:.6f}")

        # Verify model configs exist
        assert "claude-3-haiku-20240307" in MODEL_CONFIGS
        assert "gpt-4o-mini" in MODEL_CONFIGS
        assert "gemini-2.0-flash" in MODEL_CONFIGS
        print(f"✓ Model configs loaded: {len(MODEL_CONFIGS)} models")

        return True

    except Exception as e:
        print(f"✗ Pricing validation failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("RUNNER MODULE VALIDATION")
    print("=" * 60)

    results = []

    results.append(("Import Test", validate_imports()))
    results.append(("Config Creation", validate_config_creation()))
    results.append(("TestResult Structure", validate_test_result_structure()))
    results.append(("Aggregator Functions", validate_aggregator()))
    results.append(("Pricing Functions", validate_pricing()))

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(r[1] for r in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
    else:
        print("✗ SOME VALIDATIONS FAILED")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
