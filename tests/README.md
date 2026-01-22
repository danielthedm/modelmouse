# Tests

Unit tests for modelmouse core functionality.

## Running Tests

Install dependencies first:
```bash
pip install -e .
pip install pytest
```

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_scoring.py -v
```

Run with coverage:
```bash
pytest --cov=modelmouse --cov-report=html
```

## Test Coverage

- **test_scoring.py** - Scoring algorithm tests (0-100 scoring system)
- **test_models.py** - Model catalog and metadata tests
- **test_schemas.py** - Pydantic schema validation tests

## Future Tests

Additional test coverage needed for:
- Provider service integration tests (with mocked APIs)
- Runner/executor orchestration tests
- CLI command tests
- File I/O operations
- Progress display
