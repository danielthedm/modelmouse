# modelmouse

Standalone CLI tool for LLM model benchmarking and recommendations. Test multiple models across providers, compare performance with scoring, and find the best model for your use case.

## Features

- **Full Benchmarking** - Test models with schematized (JSON) or unschematized (text) outputs
- **6 Providers** - Anthropic, OpenAI, Google, Mistral, DeepSeek, Groq (45+ models)
- **Sophisticated Scoring** - Nuanced 0-100 scoring with attribute-level analysis
- **AI Judge** - Optional LLM-as-judge evaluation for additional accuracy insights
- **Document Support** - Test with PDFs, images, and text inputs
- **Three Modes** - Quick (single config), Standard (3 configs), Sweep (automatic optimization)
- **AI Recommendations** - Get intelligent model suggestions based on your task
- **Cost Tracking** - Monitor token usage and estimated costs
- **No Database** - Results saved to JSON files, no setup required

## Installation

```bash
pip install modelmouse
```

Or install from source:

```bash
git clone https://github.com/yourusername/modelmouse.git
cd modelmouse
pip install -e .
```

## Quick Start

### 1. Run Quick Tests (Easiest!)

Test with included examples - no file setup required:

```bash
# Invoice extraction from PDFs (vision models)
modelmouse test-invoice --anthropic $ANTHROPIC_API_KEY --openai $OPENAI_API_KEY

# Sentiment analysis (text generation with AI Judge)
modelmouse test-sentiment --anthropic $ANTHROPIC_API_KEY --openai $OPENAI_API_KEY
```

These commands use the bundled example files automatically!

### 2. Test Your API Keys

```bash
modelmouse test-keys \
  --anthropic sk-ant-... \
  --openai sk-... \
  --google ...
```

### 3. List Available Models

```bash
# All models
modelmouse list-models

# Filter by provider
modelmouse list-models --provider anthropic
```

### 4. Get Model Recommendations

```bash
modelmouse recommend \
  --task "Extract invoice data from PDFs" \
  --schema invoice_schema.json \
  --tests sample_tests.json \
  --anthropic sk-ant-...
```

### 5. Run a Custom Benchmark

```bash
modelmouse benchmark \
  --task "Extract structured data from invoices" \
  --schema invoice_schema.json \
  --tests invoice_tests.json \
  --models claude-sonnet-4-5-20250929 \
  --models gpt-4o \
  --mode quick \
  --output results.json \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY
```

## Commands

### test-invoice

Quick test using bundled invoice PDFs (no file setup needed).

```bash
modelmouse test-invoice \
  --anthropic sk-ant-... \
  --openai sk-... \
  [--output results.json]
```

**What it does:**
- Tests 3 vision models on PDF invoice extraction
- Uses 3 sample invoice PDFs included with modelmouse
- Extracts invoice number, date, vendor, total, and line items
- Shows accuracy, speed, and cost metrics

**Models tested:**
- claude-sonnet-4-5-20250929
- gpt-4o
- gemini-2.5-flash

### test-sentiment

Quick test using bundled review text (no file setup needed).

```bash
modelmouse test-sentiment \
  --anthropic sk-ant-... \
  --openai sk-... \
  [--output results.json]
```

**What it does:**
- Tests models on sentiment analysis (unschematized)
- Uses 4 sample product reviews
- AI Judge evaluation enabled automatically
- Shows both algorithm and judge scores

**Models tested:**
- claude-haiku-4-5-20251001
- gpt-4o-mini

### test-keys

Test API connections for each provider.

```bash
modelmouse test-keys \
  --anthropic sk-ant-... \
  --openai sk-... \
  --google ... \
  --mistral ... \
  --deepseek ... \
  --groq ...
```

**Output:**
- Connection status for each provider
- Number of available models
- Error messages if connection fails

### list-models

List all available models with capabilities.

```bash
# All models
modelmouse list-models

# Specific provider
modelmouse list-models --provider anthropic

# JSON output
modelmouse list-models --json
```

**Output:**
- Model ID and provider
- Vision support
- JSON schema support
- Context window size

### recommend

Get AI-powered model recommendations.

```bash
modelmouse recommend \
  --task "Your task description" \
  --schema schema.json \
  [--tests tests.json] \
  [--anthropic sk-ant-...]
```

**Options:**
- `--task` - Description of your use case (required)
- `--schema` - JSON schema file for expected output
- `--tests` - Test cases file (optional)
- `--anthropic` - API key for AI recommendations

**Output:**
- 3-5 recommended models with reasoning
- Confidence level for each recommendation
- Overall recommendation strategy

### benchmark

Run comprehensive benchmarks across multiple models.

```bash
modelmouse benchmark \
  --task "Task description" \
  --schema schema.json \
  --tests tests.json \
  --models model1 \
  --models model2 \
  --mode quick|standard|sweep \
  [--sweep-params sweep.json] \
  [--output results.json] \
  [--format json|table|csv] \
  [--anthropic sk-ant-...] \
  [--openai sk-...] \
  [--google ...] \
  [--mistral ...] \
  [--deepseek ...] \
  [--groq ...]
```

**Options:**
- `--task` - Task description/prompt (required)
- `--schema` - JSON schema file for structured output
- `--tests` - Test cases file (required)
- `--models` - Model IDs to test (can specify multiple)
- `--mode` - Testing mode: `quick`, `standard`, or `sweep`
- `--sweep-params` - Custom parameters for sweep mode
- `--output` - Output file path (default: timestamped in results/)
- `--format` - Output format: `json`, `table`, or `csv`

**Benchmark Modes:**

1. **Quick** - Single deterministic config (temp=0)
   - Fastest option for model comparison
   - 1 test per model

2. **Standard** - Three temperature configs (0, 0.5, 1.0)
   - See model behavior across temperatures
   - 3 tests per model

3. **Sweep** - Two-phase automatic optimization
   - Phase 1: Test all models with temp=0
   - Phase 2: Sweep top N models with custom parameters
   - Finds optimal configuration automatically

**Output:**
- Real-time progress display
- Per-test results with scores
- Aggregate statistics
- Best/fastest/cheapest model rankings
- Results saved to file

## API Key Management

API keys can be provided in three ways (priority order):

1. **CLI Arguments**
   ```bash
   modelmouse benchmark --anthropic sk-ant-... --openai sk-...
   ```

2. **Environment Variables**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   export OPENAI_API_KEY=sk-...
   export GOOGLE_API_KEY=...
   export MISTRAL_API_KEY=...
   export DEEPSEEK_API_KEY=...
   export GROQ_API_KEY=...
   ```

3. **Config File** (optional)
   ```yaml
   # ~/.modelmouse/config.yaml
   api_keys:
     anthropic: sk-ant-...
     openai: sk-...
     google: ...
   ```

## File Formats

### Schema File (schema.json)

JSON schema for expected output:

```json
{
  "type": "object",
  "properties": {
    "invoice_number": {"type": "string"},
    "date": {"type": "string"},
    "total": {"type": "number"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": {"type": "string"},
          "quantity": {"type": "integer"},
          "price": {"type": "number"}
        }
      }
    }
  },
  "required": ["invoice_number", "date", "total"]
}
```

### Tests File (tests.json)

Test cases with inputs and expected outputs:

```json
[
  {
    "name": "Test 1",
    "input_text": "Invoice #12345\nDate: 2024-01-15\nTotal: $150.00",
    "expected_output": {
      "invoice_number": "12345",
      "date": "2024-01-15",
      "total": 150.00,
      "items": []
    }
  },
  {
    "name": "Test 2 - PDF",
    "file_path": "invoices/invoice2.pdf",
    "expected_output": {
      "invoice_number": "67890",
      "date": "2024-01-20",
      "total": 299.99
    }
  }
]
```

### Sweep Parameters (sweep.json)

Custom parameter combinations for sweep mode:

```json
{
  "temperature": [0.0, 0.5, 1.0],
  "top_p": [0.9, 1.0],
  "max_tokens": [2048, 4096]
}
```

## Scoring System

modelmouse uses sophisticated 0-100 scoring instead of binary pass/fail:

- **Exact Match** - 100 points
- **Case Insensitive Match** - 95 points
- **Trimmed Match** - 90 points
- **Partial String Match** - 50-70 points
- **Numeric Values** - Scored by relative difference
- **Arrays** - F1-score using precision and recall
- **Objects** - Averaged attribute scores

### Example Scores

```python
# Exact match
actual: "Invoice-123"
expected: "Invoice-123"
score: 100

# Case difference
actual: "invoice-123"
expected: "Invoice-123"
score: 95

# Numeric difference (5% off)
actual: 105.0
expected: 100.0
score: 90

# Partial array match
actual: ["A", "B"]
expected: ["A", "B", "C"]
score: 67  # (precision=100, recall=67, F1=80)
```

## Supported Models

### Anthropic
- claude-sonnet-4-5-20250929
- claude-haiku-4-5-20251001
- claude-opus-4-5-20251101
- claude-sonnet-4-20250514
- claude-3-5-haiku-20241022
- claude-3-haiku-20240307

### OpenAI
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-3.5-turbo

### Google
- gemini-2.5-pro
- gemini-2.5-flash
- gemini-2.0-flash

### Mistral
- mistral-large-latest
- mistral-medium-latest
- mistral-small-latest
- ministral-8b-latest
- ministral-3b-latest
- codestral-latest
- pixtral-large-latest (vision)
- pixtral-12b-latest (vision)
- open-mistral-nemo
- open-mixtral-8x22b
- open-mixtral-8x7b

### DeepSeek
- deepseek-chat
- deepseek-reasoner
- deepseek-coder

### Groq
- openai/gpt-oss-120b
- openai/gpt-oss-20b
- meta-llama/llama-4-scout-17b-16e-instruct
- meta-llama/llama-4-maverick-17b-128e-instruct
- llama-3.3-70b-versatile
- llama-3.1-8b-instant
- qwen/qwen3-32b

## Examples

### Invoice Extraction

```bash
modelmouse benchmark \
  --task "Extract invoice details including number, date, items, and total" \
  --schema invoice_schema.json \
  --tests invoice_tests.json \
  --models claude-sonnet-4-5-20250929 \
  --models gpt-4o \
  --models gemini-2.5-flash \
  --mode quick \
  --output invoice_results.json \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY \
  --google $GOOGLE_API_KEY
```

### Sentiment Analysis (Unschematized)

```bash
modelmouse benchmark \
  --task "Analyze sentiment and provide detailed reasoning" \
  --tests sentiment_tests.json \
  --models claude-haiku-4-5-20251001 \
  --models gpt-4o-mini \
  --mode standard \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY
```

### Resume Parsing with Sweep

```bash
modelmouse benchmark \
  --task "Extract structured data from resumes" \
  --schema resume_schema.json \
  --tests resume_tests.json \
  --models claude-sonnet-4-5-20250929 \
  --models gpt-4o \
  --models gemini-2.5-pro \
  --mode sweep \
  --sweep-params sweep_config.json \
  --anthropic $ANTHROPIC_API_KEY \
  --openai $OPENAI_API_KEY \
  --google $GOOGLE_API_KEY
```

## Results Format

Benchmark results are saved as JSON:

```json
{
  "benchmark_config": {
    "name": "Invoice Extraction",
    "mode": "quick",
    "models": ["claude-sonnet-4-5-20250929", "gpt-4o"]
  },
  "results": [
    {
      "test_name": "Test 1",
      "model": "claude-sonnet-4-5-20250929",
      "success": true,
      "overall_score": 95.5,
      "latency_ms": 1234,
      "input_tokens": 456,
      "output_tokens": 123,
      "estimated_cost": 0.0012,
      "attribute_scores": {
        "invoice_number": 100,
        "date": 100,
        "total": 95
      }
    }
  ],
  "summary": {
    "total_cost": 0.0089,
    "avg_latency_ms": 1456,
    "avg_score": 92.3,
    "best_model": "claude-sonnet-4-5-20250929",
    "fastest_model": "gpt-4o-mini",
    "cheapest_model": "gpt-4o-mini"
  }
}
```

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## License

MIT License

## Support

For issues and feature requests, please open a GitHub issue.

## AI Judge Evaluation

For additional accuracy insights, modelmouse includes an optional **AI Judge** feature that uses LLM-as-judge to evaluate results.

### When to Use AI Judge

1. **Unschematized Benchmarks** - Automatically enabled for free-form text outputs
2. **Additional Validation** - Get a second opinion on schematized outputs
3. **Qualitative Assessment** - Evaluate nuanced aspects like tone, completeness, relevance

### How It Works

The AI Judge (Claude Haiku) reviews each result and provides:
- **Score (0-100)** - How well the output meets the task requirements
- **Reasoning** - Brief explanation of the score

Example result with AI Judge:
```json
{
  "overall_score": 95.5,        // Algorithm score (schema matching)
  "judge_score": 92.0,          // AI Judge score
  "judge_reasoning": "Output correctly extracts all invoice fields with minor formatting differences in the date field."
}
```

### Enabling AI Judge

AI Judge is automatically enabled for unschematized benchmarks. For schematized benchmarks, you can enable it by setting `evaluation_mode` in your config.

**Requirements:**
- Anthropic API key (uses Claude Haiku - very cost-effective)
- Will add ~$0.0002-0.001 per evaluation depending on output size

**Note:** AI Judge provides complementary evaluation to the algorithm scores. Both metrics are useful:
- **Algorithm Score** - Precise, deterministic, attribute-level matching
- **Judge Score** - Holistic, considers context and task requirements
