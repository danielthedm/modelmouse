import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


RECOMMENDER_MODEL = "claude-3-5-haiku-20241022"

RECOMMENDATION_TOOL = {
    "name": "submit_recommendations",
    "description": "Submit model recommendations with reasoning",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "description": "Ordered list of recommended models (best first), limit to 3-5 models",
                "items": {
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "string",
                            "description": "The model ID to recommend"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief 1-2 sentence explanation of why this model is recommended for this task"
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Confidence level in this recommendation"
                        }
                    },
                    "required": ["model_id", "reasoning", "confidence"]
                }
            },
            "overall_reasoning": {
                "type": "string",
                "description": "2-3 sentence summary of the recommendation strategy and key factors considered"
            }
        },
        "required": ["recommendations", "overall_reasoning"]
    }
}


def build_recommendation_prompt(
    prompt: str,
    output_schema: Optional[Dict[str, Any]],
    benchmark_type: str,
    test_cases: List[Dict[str, Any]],
    available_models: List[Dict[str, Any]]
) -> str:
    """Build the prompt for the AI to recommend models."""

    schema_desc = "No specific output schema (free-form text output)"
    if output_schema:
        try:
            schema_desc = json.dumps(output_schema, indent=2)
        except:
            schema_desc = str(output_schema)

    test_summary = []
    for i, tc in enumerate(test_cases[:5]):
        tc_info = f"Test {i + 1}:"
        if tc.get('has_document'):
            tc_info += f" Document ({tc.get('file_type', 'unknown type')})"
        elif tc.get('input_text'):
            preview = tc['input_text'][:200] + "..." if len(tc.get('input_text', '')) > 200 else tc.get('input_text', '')
            tc_info += f" Text input: {preview}"
        if tc.get('expected_output_preview'):
            tc_info += f"\n   Expected: {tc['expected_output_preview'][:200]}..."
        test_summary.append(tc_info)

    test_summary_text = "\n".join(test_summary) if test_summary else "No test cases provided"
    if len(test_cases) > 5:
        test_summary_text += f"\n... and {len(test_cases) - 5} more test cases"

    models_info = []
    for m in available_models:
        model_desc = f"- {m['id']} ({m['provider']})"
        if m.get('name'):
            model_desc = f"- {m['name']} [{m['id']}] ({m['provider']})"

        caps = []
        if m.get('context_window'):
            caps.append(f"context: {m['context_window']:,} tokens")
        if m.get('supports_images'):
            caps.append("vision")
        if m.get('supports_pdf'):
            caps.append("PDF")
        if m.get('supports_structured_output'):
            caps.append("structured output")
        if m.get('description'):
            caps.append(m['description'][:100])

        if caps:
            model_desc += f"\n  Capabilities: {', '.join(caps)}"
        models_info.append(model_desc)

    models_text = "\n".join(models_info)

    prompt_text = f"""You are an expert AI model selector. Based on the benchmark task below, recommend the best models to use.

## Task/Prompt
{prompt}

## Output Type
{benchmark_type} benchmark
{"Expected output schema:" if output_schema else ""}
{schema_desc if output_schema else ""}

## Test Cases
{test_summary_text}

## Available Models
{models_text}

## Your Task
Recommend 3-5 models that would perform best on this task. Consider:

1. **Task Requirements**:
   - Does the task require reasoning, code generation, document analysis, or simple extraction?
   - How complex is the expected output?

2. **Model Capabilities**:
   - Vision/PDF support if documents are involved
   - Structured output support for schema-based tasks
   - Context window size for longer inputs

3. **Cost-Effectiveness**:
   - Don't always recommend the most expensive model
   - For simple tasks, faster/cheaper models may be equally effective

4. **Diversity**:
   - Include models from different providers when appropriate
   - Mix capability levels to give users options

Use the submit_recommendations tool to provide your recommendations. Order them from most recommended to least recommended.
"""
    return prompt_text


def get_model_recommendations(
    prompt: str,
    output_schema: Optional[Dict[str, Any]],
    benchmark_type: str,
    test_cases: List[Dict[str, Any]],
    available_models: List[Dict[str, Any]],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get AI-powered model recommendations for a benchmark.

    Args:
        prompt: The benchmark task/prompt
        output_schema: Expected output schema (None for unschematized)
        benchmark_type: "schematized" or "unschematized"
        test_cases: List of test case info
        available_models: List of available models
        api_key: Optional API key (if not provided, recommendations disabled)

    Returns:
        Dict with 'recommendations' list and 'overall_reasoning' string
    """
    if not api_key:
        return {
            "recommendations": [],
            "overall_reasoning": "AI recommendations unavailable - API key not provided. Use --anthropic flag to enable."
        }

    if not available_models:
        return {
            "recommendations": [],
            "overall_reasoning": "No models available for recommendation"
        }

    client = Anthropic(api_key=api_key)

    recommendation_prompt = build_recommendation_prompt(
        prompt=prompt,
        output_schema=output_schema,
        benchmark_type=benchmark_type,
        test_cases=test_cases,
        available_models=available_models
    )

    try:
        response = client.messages.create(
            model=RECOMMENDER_MODEL,
            max_tokens=2048,
            tools=[RECOMMENDATION_TOOL],
            tool_choice={"type": "tool", "name": "submit_recommendations"},
            messages=[
                {"role": "user", "content": recommendation_prompt}
            ]
        )

        result = {"recommendations": [], "overall_reasoning": ""}
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_recommendations":
                tool_input = block.input
                result["recommendations"] = tool_input.get("recommendations", [])
                result["overall_reasoning"] = tool_input.get("overall_reasoning", "")
                break

        available_ids = {m['id'] for m in available_models}
        valid_recommendations = [
            r for r in result["recommendations"]
            if r.get("model_id") in available_ids
        ]
        result["recommendations"] = valid_recommendations

        return result

    except Exception as e:
        return {
            "recommendations": [],
            "overall_reasoning": f"Error getting recommendations: {str(e)}"
        }
