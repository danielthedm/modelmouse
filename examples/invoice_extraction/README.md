# Invoice Extraction Example

This example demonstrates using modelmouse to benchmark models on extracting structured data from invoice PDFs.

## Files

- `schema.json` - JSON schema defining the expected output structure
- `tests.json` - Test cases with invoice PDFs and expected outputs
- `invoice-001.pdf` - Sample invoice 1
- `invoice-002.pdf` - Sample invoice 2
- `invoice-003.pdf` - Sample invoice 3

## Running the Benchmark

### Quick Mode (Fastest)

Test all models with a single deterministic configuration:

```bash
modelmouse benchmark \
  --task "Extract structured invoice data including invoice number, date, vendor, total, and line items" \
  --schema examples/invoice_extraction/schema.json \
  --tests examples/invoice_extraction/tests.json \
  --models claude-sonnet-4-5-20250929 \
  --models gpt-4o \
  --models gemini-2.5-flash \
  --mode quick \
  --output invoice_results.json \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY \
  --google $GOOGLE_API_KEY
```

### Standard Mode

Test with three temperature configurations:

```bash
modelmouse benchmark \
  --task "Extract structured invoice data including invoice number, date, vendor, total, and line items" \
  --schema examples/invoice_extraction/schema.json \
  --tests examples/invoice_extraction/tests.json \
  --models claude-sonnet-4-5-20250929 \
  --models gpt-4o \
  --mode standard \
  --output invoice_results.json \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY
```

### Get Recommendations First

Ask AI which models to test:

```bash
modelmouse recommend \
  --task "Extract structured invoice data from PDFs" \
  --schema examples/invoice_extraction/schema.json \
  --tests examples/invoice_extraction/tests.json \
  --anthropic $ANTHROPIC_API_KEY
```

## Expected Results

The benchmark will test each model's ability to:
- Extract invoice numbers
- Parse dates accurately
- Identify vendor names
- Calculate totals correctly
- Extract line items (if present)

Results include:
- **Accuracy scores** (0-100) for each field
- **Latency** in milliseconds
- **Cost** estimates based on token usage
- **Aggregate stats** showing best/fastest/cheapest model

## Example Output

```json
{
  "results": [
    {
      "model": "claude-sonnet-4-5-20250929",
      "test_name": "Invoice 1 - PDF",
      "overall_score": 98.5,
      "latency_ms": 1234,
      "estimated_cost": 0.0045,
      "attribute_scores": {
        "invoice_number": 100,
        "date": 100,
        "vendor": 95,
        "total": 100
      }
    }
  ],
  "summary": {
    "avg_score": 96.7,
    "avg_latency_ms": 1456,
    "total_cost": 0.0123,
    "best_model": "claude-sonnet-4-5-20250929",
    "fastest_model": "gpt-4o-mini",
    "cheapest_model": "gemini-2.5-flash"
  }
}
```
