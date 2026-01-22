# modelmouse Examples

This directory contains real-world examples demonstrating different use cases for modelmouse.

## Available Examples

### 1. Invoice Extraction (Schematized + Documents)
**Directory:** `invoice_extraction/`

Demonstrates:
- Extracting structured data from PDF invoices
- Using JSON schemas for validation
- Vision-capable models (Claude, GPT-4o, Gemini)
- Document processing

**Run it:**
```bash
cd invoice_extraction
modelmouse benchmark \
  --task "Extract invoice data" \
  --schema schema.json \
  --tests tests.json \
  --models claude-sonnet-4-5-20250929 \
  --models gpt-4o \
  --mode quick \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY
```

### 2. Sentiment Analysis (Unschematized)
**Directory:** `sentiment_analysis/`

Demonstrates:
- Free-form text generation
- AI Judge evaluation
- No JSON schema required
- Comparing model reasoning quality

**Run it:**
```bash
cd sentiment_analysis
modelmouse benchmark \
  --task "Analyze sentiment and explain" \
  --tests tests.json \
  --models claude-haiku-4-5-20251001 \
  --models gpt-4o-mini \
  --mode quick \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY
```

## Example Types

### Schematized Benchmarks
- Enforce JSON schema on outputs
- Score based on field-level accuracy
- Examples: data extraction, classification, structured analysis
- Use `--schema schema.json`

### Unschematized Benchmarks
- Free-form text outputs
- Evaluated with AI Judge
- Examples: summarization, creative writing, explanations
- No schema required

## Creating Your Own Examples

1. **Create a directory** for your use case
2. **Define schema.json** (for schematized) or skip for unschematized
3. **Create tests.json** with test cases:
   ```json
   [
     {
       "name": "Test 1",
       "input_text": "Your input...",
       "expected_output": {...}
     }
   ]
   ```
4. **Run benchmark** with your preferred models and mode

## File Structure

Each example should include:
- `README.md` - Documentation and usage
- `schema.json` - JSON schema (schematized only)
- `tests.json` - Test cases
- Sample files (PDFs, images, etc.) if needed

## Need Help?

Check the main README for:
- Complete command reference
- API key setup
- Output format details
- Troubleshooting
