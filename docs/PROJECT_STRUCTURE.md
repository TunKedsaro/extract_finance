# Project structure

```text
extract_finance/
├── src/app/
│   ├── main.py                         # FastAPI app and exception handlers
│   ├── cli.py                          # Command-line adapter
│   ├── api/
│   │   ├── dependencies.py             # Dependency construction
│   │   └── routes/
│   │       ├── health.py
│   │       └── extraction.py
│   ├── core/
│   │   ├── config.py                   # Environment-backed settings
│   │   ├── exceptions.py               # Application error taxonomy
│   │   └── logging.py
│   ├── models/
│   │   ├── api.py                      # Request/error/health schemas
│   │   └── extraction.py               # LLM and public response schemas
│   ├── services/
│   │   ├── extraction_service.py       # Extraction orchestrator
│   │   └── document_parser.py          # PDF/XLSX preprocessing
│   ├── infrastructure/llm/
│   │   └── anthropic_client.py         # Terrax/LiteLLM adapter
│   └── prompts/
│       ├── extraction_system.md
│       └── extraction_user.md
├── resources/input/                    # Local source documents (ignored by Git)
├── outputs/                            # Persisted JSON results (ignored by Git)
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Runtime flow

```text
POST /api/v1/extractions or CLI
                │
                ▼
        ExtractionService
        ├── resolve path under INPUT_DIR
        ├── enforce type and size limits
        ├── DocumentParser
        │   ├── PDF: text page or rendered JPEG
        │   └── XLSX: flattened text with column indentation
        ├── AnthropicLLMClient
        ├── validate FinancialStatementData
        ├── derive quarter/reported_date
        └── optionally persist JSON atomically
                │
                ▼
    FinancialExtractionResult
```

## Layer responsibilities

### API and CLI adapters

Adapters accept user input, call `ExtractionService`, and format the result. They do not
parse documents or call Claude directly. `cli.py` is therefore not the parser.

### Services

`DocumentParser` owns format-specific preprocessing. `ExtractionService` owns the use-case
flow, including safe path resolution, prompt loading, validation, deterministic fields,
and optional output persistence.

### Models

`FinancialStatementData` is sent to Claude as JSON Schema and deliberately excludes
`quarter` and `reported_date`. `FinancialExtractionResult` is the fixed public contract;
optional values are serialized as `null` rather than omitted.

### Infrastructure

`AnthropicLLMClient` contains provider-specific authentication and SDK calls. It uses direct
Terrax access when `ANTHROPIC_AUTH_TOKEN` is set, otherwise it uses the LiteLLM proxy.

## Security boundary

API and CLI paths are resolved beneath `INPUT_DIR`. Absolute paths, `..` traversal, and
symlinks that resolve outside that directory are rejected. This prevents a caller from
using the API to read `.env` or unrelated server files.
