"""Tests for schemas and validation."""
import pytest
from pydantic import ValidationError
from modelmouse.core.schemas import BenchmarkConfig, TestCase
from modelmouse.core.types import BenchmarkMode, BenchmarkType, EvaluationMode


class TestBenchmarkConfig:
    def test_valid_schematized_config(self):
        config = BenchmarkConfig(
            prompt="Test prompt",
            output_schema={"type": "object", "properties": {}},
            tests=[],
            models=["claude-sonnet-4-5-20250929"],
            mode=BenchmarkMode.QUICK,
            benchmark_type=BenchmarkType.SCHEMATIZED,
        )
        assert config.benchmark_type == BenchmarkType.SCHEMATIZED
        assert config.output_schema is not None

    def test_schematized_requires_schema(self):
        with pytest.raises(ValidationError):
            BenchmarkConfig(
                prompt="Test prompt",
                output_schema=None,
                tests=[],
                models=["claude-sonnet-4-5-20250929"],
                benchmark_type=BenchmarkType.SCHEMATIZED,
            )

    def test_unschematized_no_schema(self):
        config = BenchmarkConfig(
            prompt="Test prompt",
            output_schema=None,
            tests=[],
            models=["claude-sonnet-4-5-20250929"],
            benchmark_type=BenchmarkType.UNSCHEMATIZED,
        )
        assert config.evaluation_mode == EvaluationMode.AI_JUDGE

    def test_unschematized_auto_sets_ai_judge(self):
        config = BenchmarkConfig(
            prompt="Test prompt",
            output_schema=None,
            tests=[],
            models=["claude-sonnet-4-5-20250929"],
            benchmark_type=BenchmarkType.UNSCHEMATIZED,
            evaluation_mode=EvaluationMode.SCHEMA_MATCH,
        )
        assert config.evaluation_mode == EvaluationMode.AI_JUDGE


class TestTestCase:
    def test_text_input(self):
        test = TestCase(
            name="Test 1",
            input_text="Hello world",
            expected_output={"result": "hello"}
        )
        assert test.input_text == "Hello world"
        assert test.file_path is None

    def test_file_input(self):
        test = TestCase(
            name="Test PDF",
            file_path="/path/to/file.pdf",
            file_type="application/pdf",
            expected_output={"result": "data"}
        )
        assert test.file_path == "/path/to/file.pdf"
        assert test.input_text is None

    def test_combined_input(self):
        test = TestCase(
            name="Combined",
            input_text="Context",
            file_path="/path/to/file.pdf",
            expected_output={}
        )
        assert test.input_text is not None
        assert test.file_path is not None
