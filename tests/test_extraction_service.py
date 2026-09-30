import asyncio
import json
from datetime import date
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import (
    InputFileNotFoundError,
    InvalidInputPathError,
    UnsupportedDocumentTypeError,
)
from app.services.document_parser import PDF_MIME_TYPE
from app.services.extraction_service import ExtractionService, quarter_from_date


class FakeParser:
    def mime_type_for(self, file_path: Path) -> str:
        if file_path.suffix.lower() != ".pdf":
            raise UnsupportedDocumentTypeError()
        return PDF_MIME_TYPE

    def to_content_blocks(self, file_bytes: bytes, mime_type: str) -> list[dict]:
        assert file_bytes == b"fake-pdf"
        assert mime_type == PDF_MIME_TYPE
        return [{"type": "text", "text": "financial statement"}]


class FakeLLM:
    def __init__(self) -> None:
        self.call: dict | None = None

    def generate_from_blocks(self, **kwargs) -> str:
        self.call = kwargs
        return json.dumps(
            {
                "metadata": {
                    "company_name": "Example Public Company Limited",
                    "financial_date": "31 March 2026",
                    "financial_date_iso": "2026-03-31",
                },
                "balance_sheet": {
                    "cash": None,
                    "asset": 1000,
                    "liabilities": 600,
                    "equity": 400,
                },
                "income_statement": {
                    "revenue": 500,
                    "expense": None,
                    "operating_profit": None,
                    "ebit": None,
                    "ebitda": None,
                    "net_profit": 25,
                },
            }
        )


def build_service(tmp_path: Path) -> tuple[ExtractionService, FakeLLM]:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    settings = Settings(
        _env_file=None,
        input_dir=input_dir,
        output_dir=output_dir,
        save_output=True,
    )
    llm = FakeLLM()
    service = ExtractionService(
        settings=settings,
        parser=FakeParser(),
        llm_client=llm,
        date_provider=lambda: date(2026, 9, 30),
    )
    return service, llm


def test_extracts_validates_derives_and_saves_output(tmp_path: Path) -> None:
    service, llm = build_service(tmp_path)
    (service.settings.input_directory / "statement.pdf").write_bytes(b"fake-pdf")

    result = asyncio.run(
        service.extract_from_input("statement.pdf", transaction_id="test-001")
    )

    assert result.metadata.company_name == "Example Public Company Limited"
    assert result.quarter == "Q1 2026"
    assert result.reported_date == date(2026, 9, 30)
    assert llm.call is not None
    assert llm.call["metadata"] == {"transaction_id": "test-001"}
    assert "quarter" not in llm.call["response_schema"]["properties"]

    saved = json.loads(
        (service.settings.output_directory / "statement.json").read_text()
    )
    assert saved == result.model_dump(mode="json")
    assert saved["balance_sheet"]["cash"] is None


def test_path_must_remain_inside_input_directory(tmp_path: Path) -> None:
    service, _ = build_service(tmp_path)
    outside_file = tmp_path / "secret.pdf"
    outside_file.write_bytes(b"fake-pdf")

    with pytest.raises(InvalidInputPathError):
        service.resolve_input_path("../secret.pdf")

    with pytest.raises(InvalidInputPathError):
        service.resolve_input_path(str(outside_file))

    with pytest.raises(InputFileNotFoundError):
        service.resolve_input_path("missing.pdf")


def test_quarter_is_a_deterministic_calendar_calculation() -> None:
    assert quarter_from_date(date(2026, 1, 1)) == "Q1 2026"
    assert quarter_from_date(date(2026, 6, 30)) == "Q2 2026"
    assert quarter_from_date(date(2026, 9, 30)) == "Q3 2026"
    assert quarter_from_date(date(2026, 12, 31)) == "Q4 2026"
    assert quarter_from_date(None) is None
