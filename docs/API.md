# API reference

## `GET /health`

Confirms that the HTTP process is running. It does not call the configured LLM.

```json
{
  "status": "ok",
  "service": "Financial Statement Extraction API",
  "version": "0.1.0"
}
```

## `POST /api/v1/extractions`

Starts a synchronous extraction. The request remains open while the document is parsed and
the LLM responds.

Request:

```json
{
  "input_path": "statement.pdf"
}
```

`input_path` is relative to `INPUT_DIR`. Supported extensions are `.pdf`, `.xlsx`,
and `.docx`.
The optional `X-Transaction-ID` header is included in logs and upstream request metadata.

Success returns HTTP 200 and a `FinancialExtractionResult` directly, without a wrapper.
All schema fields are present; unavailable financial values are `null`.

## Error format

```json
{
  "error": {
    "code": "input_file_not_found",
    "message": "The requested input file does not exist."
  }
}
```

Common status codes:

| Status | Meaning |
|---:|---|
| 400 | Path is absolute or escapes `INPUT_DIR` |
| 404 | Input file does not exist |
| 413 | Input exceeds `MAX_INPUT_FILE_SIZE_BYTES` |
| 415 | Extension is not PDF/XLSX/DOCX |
| 422 | Request payload or source document is invalid |
| 500 | Configuration or output persistence failed |
| 502 | LLM call failed or returned data outside the schema |
