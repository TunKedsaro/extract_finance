# Financial Statement Extraction API

Proof of concept (POC) for extracting balance sheet and income statement data from PDF, XLSX, and DOCX files.

## Quick start

Requires Python 3.12+ and an Anthropic-compatible API credential.

```bash
git clone https://github.com/TunKedsaro/extract_finance.git
cd extract_finance
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `ANTHROPIC_AUTH_TOKEN` in `.env` (or configure the LiteLLM variables), then run:

```bash
uvicorn src.app.main:app --reload --port 8000
```

Open <http://localhost:8000/docs> or send a request to `POST /api/v1/extractions`.
The included sample files are already in `resources/input/`.

## Input payloads

PDF:

```json
{"input_path": "CP ALL Financial Statement Q1 2026.pdf"}
```

XLSX:

```json
{"input_path": "PTT Financial Statement - Q1 2026.XLSX"}
```

DOCX:

```json
{"input_path": "CP_ALL_Financial_Statement_Q1_2026_editable.docx"}
```

Example:

```bash
curl -X POST http://localhost:8000/api/v1/extractions \
  -H 'Content-Type: application/json' \
  -H 'X-Transaction-ID: poc-001' \
  -d '{"input_path":"PTT Financial Statement - Q1 2026.XLSX"}'
```

Run tests with `pytest`.
