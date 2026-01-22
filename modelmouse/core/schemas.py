from typing import Optional, List, Any, Dict
from pydantic import BaseModel, model_validator
from .types import BenchmarkMode, BenchmarkType, EvaluationMode


class TestCase(BaseModel):
    """A single test case for benchmarking."""
    name: Optional[str] = None
    input_text: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    expected_output: Optional[Any] = None


class BenchmarkConfig(BaseModel):
    """Configuration for a benchmark run."""
    name: Optional[str] = None
    description: Optional[str] = None
    benchmark_type: BenchmarkType = BenchmarkType.SCHEMATIZED
    prompt: str
    output_schema: Optional[Dict[str, Any]] = None
    mode: BenchmarkMode = BenchmarkMode.QUICK
    evaluation_mode: EvaluationMode = EvaluationMode.SCHEMA_MATCH
    tests: List[TestCase] = []
    models: List[str] = []
    sweep_parameters: Optional[Dict[str, List[float]]] = None

    @model_validator(mode='after')
    def validate_benchmark_type_constraints(self):
        if self.benchmark_type == BenchmarkType.SCHEMATIZED:
            if not self.output_schema:
                raise ValueError('output_schema is required for schematized benchmarks')
            if not isinstance(self.output_schema, dict):
                raise ValueError('output_schema must be a valid JSON schema object')
        elif self.benchmark_type == BenchmarkType.UNSCHEMATIZED:
            if self.output_schema:
                raise ValueError('output_schema must be null for unschematized benchmarks')
            if self.evaluation_mode != EvaluationMode.AI_JUDGE:
                self.evaluation_mode = EvaluationMode.AI_JUDGE
        return self


class TestResult(BaseModel):
    """Result of running a single test."""
    test_name: Optional[str] = None
    model: str
    preset: str
    preset_name: str
    temperature: float
    top_p: float
    max_tokens: int
    success: bool
    input_text: Optional[str] = None
    file_name: Optional[str] = None
    prompt: str
    expected_output: Optional[Any] = None
    output: Optional[Any] = None
    output_text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    stop_reason: Optional[str] = None
    exact_match: Optional[bool] = None
    overall_score: Optional[float] = None
    attribute_scores: Optional[Dict[str, float]] = None
    attribute_matches: Optional[Dict[str, bool]] = None
    error: Optional[str] = None
    total_tokens: Optional[int] = None
    tokens_per_second: Optional[float] = None
    estimated_cost: Optional[float] = None
    judge_score: Optional[float] = None
    judge_reasoning: Optional[str] = None


class BenchmarkRun(BaseModel):
    """Complete results of a benchmark run."""
    benchmark_config: BenchmarkConfig
    mode: str
    models_tested: List[str]
    status: str = "completed"
    results: List[TestResult] = []
    total_cost: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    avg_score: Optional[float] = None
    best_model: Optional[str] = None
    fastest_model: Optional[str] = None
    cheapest_model: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
