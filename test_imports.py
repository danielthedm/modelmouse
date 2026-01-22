#!/usr/bin/env python3
"""
Test that all modules can be imported correctly.
"""

import sys
import traceback

def test_imports():
    """Test importing all main modules."""
    tests = [
        ("Core types", "from modelmouse.core import BenchmarkMode, BenchmarkType"),
        ("Core models", "from modelmouse.core import MODEL_CATALOG, get_all_models"),
        ("Core config", "from modelmouse.core import QUICK_CONFIGS, STANDARD_CONFIGS"),
        ("Schemas", "from modelmouse.core.schemas import BenchmarkConfig, TestCase"),
        ("Services", "from modelmouse.services import AnthropicService, OpenAIService"),
        ("Scoring", "from modelmouse.services.scoring import score_value, compare_outputs"),
        ("Utils", "from modelmouse.utils import save_json, load_json"),
        ("Formatters", "from modelmouse.utils.formatters import format_table"),
        ("Pricing", "from modelmouse.utils.pricing import calculate_cost"),
    ]

    print("Testing module imports...\n")
    passed = 0
    failed = 0

    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {str(e)}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
