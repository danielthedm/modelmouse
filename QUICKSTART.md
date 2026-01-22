# Quick Start Guide

Get started with modelmouse in 5 minutes using the included examples.

## 1. Install

```bash
cd /Users/danielleslie/Github/modelmouse
pip install -e .
```

## 2. Set Your API Keys

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GOOGLE_API_KEY=...
```

## 3. Test Your Keys

```bash
modelmouse test-keys --anthropic $ANTHROPIC_API_KEY --openai $OPENAI_API_KEY
```

## 4. Run Your First Benchmark

### Quick Test Commands (Easiest!)

Use the bundled examples - no file paths needed:

```bash
# Invoice extraction from PDFs
modelmouse test-invoice

# Sentiment analysis with AI Judge
modelmouse test-sentiment
```

These automatically use the included example files!

### Invoice Extraction (Full Command)

Or use the full benchmark command with explicit paths:

```bash
modelmouse benchmark \
  --task "Extract invoice details including invoice number, date, vendor, and total" \
  --schema examples/invoice_extraction/schema.json \
  --tests examples/invoice_extraction/tests.json \
  --models claude-sonnet-4-5-20250929 \
  --models gpt-4o \
  --mode quick
```

**What you'll see:**
- ✅ Real-time progress as models process 3 invoice PDFs
- 📊 Accuracy scores (0-100) for each field
- ⚡ Latency measurements
- 💰 Cost estimates
- 🏆 Best/fastest/cheapest model rankings

### Sentiment Analysis (Text Generation)

Compare models on free-form text tasks:

```bash
modelmouse benchmark \
  --task "Analyze the sentiment and explain your reasoning" \
  --tests examples/sentiment_analysis/tests.json \
  --models claude-haiku-4-5-20251001 \
  --models gpt-4o-mini \
  --mode quick
```

**What you'll see:**
- 🤖 AI Judge evaluation (automatic for unschematized)
- 📝 Qualitative assessment of responses
- 🎯 Both algorithm and judge scores

## 5. Get Model Recommendations

Not sure which models to test? Ask AI:

```bash
modelmouse recommend \
  --task "Extract structured data from PDF invoices" \
  --schema examples/invoice_extraction/schema.json \
  --tests examples/invoice_extraction/tests.json
```

## 6. View Your Results

Results are saved to JSON files in `results/` directory:

```bash
cat results/benchmark_*.json | jq '.summary'
```

## Next Steps

### Try Different Modes

**Standard Mode** - Test 3 temperature configurations:
```bash
modelmouse benchmark ... --mode standard
```

**Sweep Mode** - Automatic optimization (tests all models, then sweeps top performers):
```bash
modelmouse benchmark ... --mode sweep
```

### Compare More Models

Add models from different providers:
```bash
--models claude-sonnet-4-5-20250929 \
--models gpt-4o \
--models gemini-2.5-pro \
--models mistral-large-latest \
--models deepseek-chat
```

### Create Your Own Benchmarks

1. Copy an example directory
2. Modify `schema.json` (for structured tasks)
3. Update `tests.json` with your test cases
4. Run the benchmark!

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "API key not provided" error
Make sure environment variables are set:
```bash
echo $ANTHROPIC_API_KEY
```

### "File not found" error
Run from the modelmouse root directory or use absolute paths.

## Example Commands

### List all available models
```bash
modelmouse list-models
```

### Filter by provider
```bash
modelmouse list-models --provider anthropic
```

### Get JSON output
```bash
modelmouse benchmark ... --format json > results.json
```

### Save to custom location
```bash
modelmouse benchmark ... --output my_results.json
```

## Complete Documentation

See [README.md](README.md) for:
- Complete command reference
- File format specifications
- Scoring system details
- All 45+ supported models
