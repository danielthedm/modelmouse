# modelmouse Feature Summary

Complete feature comparison showing everything extracted from Modelator.

## ✅ Core Features

| Feature | Status | Details |
|---------|--------|---------|
| **6 Providers** | ✅ Complete | Anthropic, OpenAI, Google, Mistral, DeepSeek, Groq |
| **45+ Models** | ✅ Complete | Full catalog with metadata (vision, schema, context) |
| **Sophisticated Scoring** | ✅ Complete | 0-100 scoring with attribute-level analysis |
| **AI Judge** | ✅ Complete | LLM-as-judge evaluation (Claude Haiku) |
| **Document Support** | ✅ Complete | PDFs, images (PNG, JPEG, GIF, WebP) |
| **Three Modes** | ✅ Complete | Quick, Standard, Sweep (with 2-phase optimization) |
| **Cost Tracking** | ✅ Complete | Token counting + pricing for all models |
| **Speed Tracking** | ✅ Complete | Latency measurement in milliseconds |
| **AI Recommendations** | ✅ Complete | Model suggestions based on task requirements |
| **No Database** | ✅ Complete | File-based storage (JSON) |

## 📊 Evaluation Capabilities

### Algorithm Scoring (0-100)
- ✅ String similarity with n-gram matching
- ✅ Numeric values (relative difference)
- ✅ Arrays (F1-score: precision + recall)
- ✅ Objects (attribute-level scoring)
- ✅ Exact match detection
- ✅ Case-insensitive matching
- ✅ Partial match scoring

### AI Judge
- ✅ Automatic for unschematized benchmarks
- ✅ Optional for schematized benchmarks
- ✅ Provides 0-100 score + reasoning
- ✅ Holistic task completion assessment
- ✅ Quality and relevance evaluation

### Metrics Calculated
- ✅ Overall accuracy score
- ✅ Attribute-level scores
- ✅ Latency (milliseconds)
- ✅ Cost (USD per test)
- ✅ Tokens (input/output)
- ✅ Tokens per second
- ✅ Best/fastest/cheapest model rankings

## 🎯 Benchmark Types

| Type | Status | Description |
|------|--------|-------------|
| **Schematized** | ✅ Complete | JSON schema validation + extraction |
| **Unschematized** | ✅ Complete | Free-form text with AI Judge |
| **Text Input** | ✅ Complete | Plain text test cases |
| **Document Input** | ✅ Complete | PDF, image files |
| **Combined Input** | ✅ Complete | Text + document together |

## 🚀 Execution Modes

### Quick Mode
- ✅ Single deterministic config (temp=0)
- ✅ Fastest for model comparison
- ✅ 1 test per model

### Standard Mode
- ✅ Three temperature configs (0, 0.5, 1.0)
- ✅ Shows model behavior variation
- ✅ 3 tests per model

### Sweep Mode
- ✅ Two-phase automatic optimization
- ✅ Phase 1: Test all models (temp=0)
- ✅ Phase 2: Sweep top N with custom params
- ✅ Finds optimal configuration

## 🔧 CLI Commands

| Command | Status | Purpose |
|---------|--------|---------|
| `test-keys` | ✅ Complete | Test API connections |
| `list-models` | ✅ Complete | Show all 45+ models with capabilities |
| `recommend` | ✅ Complete | Get AI-powered model recommendations |
| `benchmark` | ✅ Complete | Run full custom benchmarks |
| `test-invoice` | ✅ Complete | Quick test with bundled invoice PDFs |
| `test-sentiment` | ✅ Complete | Quick test with bundled reviews |
| `version` | ✅ Complete | Show version info |

## 📁 File Support

### Input Formats
- ✅ JSON schemas
- ✅ JSON test cases
- ✅ PDF documents
- ✅ Images (PNG, JPEG, GIF, WebP)
- ✅ Text files
- ✅ YAML config (future)

### Output Formats
- ✅ JSON (full results)
- ✅ Table (formatted terminal output)
- ✅ CSV (spreadsheet export)
- ✅ Summary statistics

## 🎨 User Experience

### Progress Display
- ✅ Real-time progress bars (Rich library)
- ✅ Live results table
- ✅ Success/failure indicators
- ✅ Current model/test display
- ✅ Final summary with rankings

### Error Handling
- ✅ Clear error messages
- ✅ Validation before execution
- ✅ Retry logic for rate limits
- ✅ Graceful degradation
- ✅ Helpful troubleshooting hints

### Documentation
- ✅ Comprehensive README
- ✅ Quick Start guide
- ✅ Command examples
- ✅ Real-world examples with data
- ✅ API reference

## 📦 Examples Included

### Invoice Extraction
- ✅ 3 sample PDF invoices
- ✅ JSON schema
- ✅ Test cases with expected outputs
- ✅ Complete README
- ✅ Demonstrates vision + structured extraction

### Sentiment Analysis
- ✅ 4 sample product reviews
- ✅ Test cases with reference answers
- ✅ Complete README
- ✅ Demonstrates unschematized + AI Judge

### Code Examples
- ✅ Python API usage example
- ✅ Validation script
- ✅ Custom integration examples

## 🔐 API Key Management

- ✅ CLI arguments (`--anthropic`, `--openai`, etc.)
- ✅ Environment variables (`ANTHROPIC_API_KEY`, etc.)
- ✅ Config file support (planned)
- ✅ Validation before execution
- ✅ Clear error messages

## 🌟 Vision Model Support

14 models with vision capabilities:

**Anthropic (6):**
- ✅ All Claude 4.5, 4, 3.5, 3 models

**OpenAI (3):**
- ✅ GPT-4o, GPT-4o Mini, GPT-4 Turbo

**Google (3):**
- ✅ Gemini 2.5 Pro, 2.5 Flash, 2.0 Flash

**Mistral (2):**
- ✅ Pixtral Large, Pixtral 12B

## 💰 Cost Optimization

- ✅ Real-time cost estimation
- ✅ Per-model pricing data (30+ models)
- ✅ Token counting
- ✅ Cost per test
- ✅ Total cost summaries
- ✅ Cheapest model ranking
- ✅ Cost efficiency metrics

## 🎓 What's Not Included (vs Modelator Platform)

- ❌ Web UI (CLI only by design)
- ❌ User accounts / authentication
- ❌ Database storage
- ❌ API server
- ❌ Model deployment
- ❌ Production monitoring
- ❌ Team collaboration features

These are intentionally omitted - modelmouse is a standalone CLI tool, not a platform.

## 🚀 Ready to Use

Everything from Modelator's core benchmarking capabilities has been extracted:
- All provider integrations
- Complete scoring algorithms
- AI Judge evaluation
- Document processing
- Real example files
- Full CLI interface

Users can run production-quality benchmarks immediately after installation! 🎯
