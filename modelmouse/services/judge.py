import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


JUDGE_MODEL = "claude-3-5-haiku-20241022"

EVALUATION_TOOL = {
    "name": "submit_evaluations",
    "description": "Submit the evaluation scores and reasoning for each benchmark result",
    "input_schema": {
        "type": "object",
        "properties": {
            "evaluations": {
                "type": "array",
                "description": "Array of evaluations, one per result in order",
                "items": {
                    "type": "object",
                    "properties": {
                        "score": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Score from 0-100 based on how well the output matches expected"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief 1-2 sentence explanation of the score"
                        }
                    },
                    "required": ["score", "reasoning"]
                }
            }
        },
        "required": ["evaluations"]
    }
}


def build_judge_prompt(
    task_prompt: str,
    output_schema: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> str:
    """Build the prompt for the AI judge to evaluate schematized benchmark results."""

    results_text = []
    for i, result in enumerate(results):
        result_block = f"""
--- Result {i + 1} ---
Test Input: {result.get('input_text') or result.get('file_name', 'N/A')}
Expected Output: {json.dumps(result.get('expected_output'), indent=2) if result.get('expected_output') else 'Not specified'}
Model: {result.get('model')}
Actual Output: {json.dumps(result.get('output'), indent=2) if result.get('output') else 'Error or no output'}
"""
        results_text.append(result_block)

    prompt = f"""You are an expert evaluator assessing AI model outputs for a benchmark task.

## Task Description
{task_prompt}

## Expected Output Schema
{json.dumps(output_schema, indent=2)}

## Results to Evaluate
{chr(10).join(results_text)}

## Your Task
For each result, provide:
1. A score from 0-100 based on how well the output matches the expected output and task requirements
2. Brief reasoning (1-2 sentences) explaining the score

Scoring guidelines:
- 90-100: Excellent - Output is correct and matches expected values closely
- 70-89: Good - Minor differences but captures the essential information
- 50-69: Partial - Some correct elements but missing key information
- 25-49: Poor - Significant errors or missing most expected information
- 0-24: Failed - Completely wrong, invalid format, or error

Use the submit_evaluations tool to provide your evaluations. There must be exactly {len(results)} evaluations, one for each result in order.
"""
    return prompt


def build_unschematized_judge_prompt(
    task_prompt: str,
    results: List[Dict[str, Any]]
) -> str:
    """Build the prompt for the AI judge to evaluate unschematized (free-form text) benchmark results."""

    results_text = []
    for i, result in enumerate(results):
        expected_text = result.get('expected_output')
        if isinstance(expected_text, dict):
            expected_text = expected_text.get('text', json.dumps(expected_text))
        elif isinstance(expected_text, str):
            pass
        else:
            expected_text = str(expected_text) if expected_text else 'Not specified'

        actual_text = result.get('output_text') or result.get('output')
        if isinstance(actual_text, dict):
            actual_text = json.dumps(actual_text, indent=2)
        elif actual_text is None:
            actual_text = 'Error or no output'

        result_block = f"""
--- Result {i + 1} ---
Test Input: {result.get('input_text') or result.get('file_name', 'N/A')}
Reference Answer: {expected_text}
Model: {result.get('model')}
Model Output: {actual_text}
"""
        results_text.append(result_block)

    prompt = f"""You are an expert evaluator assessing AI model outputs for a free-form text task.

## Task Description
{task_prompt}

## Results to Evaluate
{chr(10).join(results_text)}

## Your Task
For each result, evaluate the model output based on:
1. **Task Completion**: Does the output accomplish what was asked?
2. **Relevance**: Is the response relevant and on-topic?
3. **Quality**: Is the response well-written, accurate, and useful?
4. **Reference Alignment** (if reference provided): How well does it align with the reference answer?

Provide:
1. A score from 0-100 based on overall quality
2. Brief reasoning (1-2 sentences) explaining the score

Scoring guidelines:
- 90-100: Excellent - Fully accomplishes the task with high quality
- 70-89: Good - Accomplishes the task with minor issues
- 50-69: Partial - Partially accomplishes the task or has notable issues
- 25-49: Poor - Fails to adequately address the task
- 0-24: Failed - Completely off-topic, wrong, or error

Use the submit_evaluations tool to provide your evaluations. There must be exactly {len(results)} evaluations, one for each result in order.
"""
    return prompt


def run_judge_evaluation(
    task_prompt: str,
    output_schema: Optional[Dict[str, Any]],
    results: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    is_unschematized: bool = False
) -> List[Dict[str, Any]]:
    """
    Run AI judge evaluation on benchmark results using structured output.

    Args:
        task_prompt: The original benchmark task/prompt
        output_schema: Expected output schema (can be None for unschematized)
        results: List of result dicts with 'input_text', 'output', 'expected_output', 'model'
        api_key: Optional API key (if not provided, judge disabled)
        is_unschematized: If True, use free-form text evaluation criteria

    Returns:
        List of dicts with 'judge_score' and 'judge_reasoning' for each result
    """
    if not api_key:
        return [{"judge_score": None, "judge_reasoning": "AI Judge unavailable - API key not provided"} for _ in results]

    if not results:
        return []

    client = Anthropic(api_key=api_key)

    if is_unschematized:
        valid_results = [r for r in results if r.get('success') and (r.get('output_text') or r.get('output') is not None)]
    else:
        valid_results = [r for r in results if r.get('success') and r.get('output') is not None]

    if not valid_results:
        return [{"judge_score": None, "judge_reasoning": None} for _ in results]

    if is_unschematized:
        prompt = build_unschematized_judge_prompt(task_prompt, valid_results)
    else:
        prompt = build_judge_prompt(task_prompt, output_schema or {}, valid_results)

    try:
        response = client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=4096,
            tools=[EVALUATION_TOOL],
            tool_choice={"type": "tool", "name": "submit_evaluations"},
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        evaluations = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_evaluations":
                tool_input = block.input
                evaluations = tool_input.get("evaluations", [])
                break

        if not evaluations:
            return [{"judge_score": None, "judge_reasoning": "Judge returned no evaluations"} for _ in results]

        final_results = []
        valid_idx = 0
        for result in results:
            has_output = result.get('success') and (result.get('output_text') or result.get('output') is not None)
            if has_output:
                if valid_idx < len(evaluations):
                    eval_data = evaluations[valid_idx]
                    final_results.append({
                        "judge_score": eval_data.get("score"),
                        "judge_reasoning": eval_data.get("reasoning")
                    })
                else:
                    final_results.append({"judge_score": None, "judge_reasoning": None})
                valid_idx += 1
            else:
                final_results.append({
                    "judge_score": None,
                    "judge_reasoning": "Skipped - result was not successful"
                })

        return final_results

    except Exception as e:
        return [{"judge_score": None, "judge_reasoning": f"Judge error: {str(e)}"} for _ in results]
