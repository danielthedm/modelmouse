# Sentiment Analysis Example

This example demonstrates using modelmouse for **unschematized benchmarks** - free-form text generation tasks that don't have a strict JSON schema.

## What's Different?

Unlike structured extraction (like invoices), sentiment analysis produces free-form text. This example shows:
- **No schema required** - Tests don't enforce JSON structure
- **AI Judge evaluation** - Automatically enabled for unschematized benchmarks
- **Text similarity scoring** - Uses semantic comparison

## Files

- `tests.json` - Test cases with review text and reference answers

## Running the Benchmark

```bash
modelmouse benchmark \
  --task "Analyze the sentiment of the following review and provide a detailed explanation of the sentiment, tone, and key points" \
  --tests examples/sentiment_analysis/tests.json \
  --models claude-haiku-4-5-20251001 \
  --models gpt-4o-mini \
  --models gemini-2.5-flash \
  --mode quick \
  --output sentiment_results.json \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY \
  --google $GOOGLE_API_KEY
```

## AI Judge Evaluation

For unschematized benchmarks, modelmouse automatically uses the **AI Judge** to evaluate results. The judge considers:
- **Task completion** - Does the output analyze sentiment?
- **Relevance** - Is the response on-topic?
- **Quality** - Is it well-written and accurate?
- **Reference alignment** - How well does it match the expected analysis?

Results include both:
- **Algorithm score** - Text similarity to reference answer
- **Judge score** - AI evaluation of quality and correctness

## Example Command

### Quick comparison of fast models:

```bash
modelmouse benchmark \
  --task "Analyze sentiment and explain reasoning" \
  --tests examples/sentiment_analysis/tests.json \
  --models claude-haiku-4-5-20251001 \
  --models gpt-4o-mini \
  --mode quick \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY
```

### Standard mode with temperature variations:

```bash
modelmouse benchmark \
  --task "Analyze sentiment and explain reasoning" \
  --tests examples/sentiment_analysis/tests.json \
  --models claude-sonnet-4-5-20250929 \
  --mode standard \
  --anthropic $ANTHROPIC_API_KEY
```

## Expected Output

```json
{
  "results": [
    {
      "model": "claude-haiku-4-5-20251001",
      "test_name": "Positive Review",
      "overall_score": 85.5,
      "judge_score": 92.0,
      "judge_reasoning": "Accurately identifies positive sentiment with supporting evidence and clear explanation.",
      "output_text": "This review exhibits strong positive sentiment...",
      "latency_ms": 823,
      "estimated_cost": 0.0008
    }
  ]
}
```
