import asyncio
import json
import logging
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from ..core.config import Settings, get_settings
from ..core.exceptions import (
    InputFileNotFoundError,
    InputFileTooLargeError,
    InvalidInputPathError,
    LLMResponseError,
    OutputWriteError,
)
from ..infrastructure.llm.anthropic_client import AnthropicLLMClient, LLMClient
from ..models.extraction import FinancialExtractionResult, FinancialStatementData
from .document_parser import DocumentParser


logger = logging.getLogger(__name__)


def quarter_from_date(financial_date: date | None) -> str | None:
    if financial_date is None:
        return None
    quarter_number = (financial_date.month - 1) // 3 + 1
    return f"Q{quarter_number} {financial_date.year}"


class ExtractionService:
    """Orchestrate safe file access, parsing, LLM extraction, and persistence."""

    def __init__(
        self,
        settings: Settings | None = None,
        parser: DocumentParser | None = None,
        llm_client: LLMClient | None = None,
        date_provider: Callable[[], date] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.parser = parser or DocumentParser()
        # Delay credential validation until a valid extraction actually reaches
        # the model-call stage. This keeps health checks and request validation
        # independent from external-service configuration.
        self.llm = llm_client
        self.date_provider = date_provider or (
            lambda: datetime.now(timezone.utc).date()
        )
        self.prompt_dir = Path(__file__).resolve().parents[1] / "prompts"

    async def extract_from_input(
        self,
        input_path: str,
        *,
        transaction_id: str | None = None,
    ) -> FinancialExtractionResult:
        request_id = transaction_id or str(uuid4())
        file_path = self.resolve_input_path(input_path)
        mime_type = self.parser.mime_type_for(file_path)

        file_size = file_path.stat().st_size
        if file_size > self.settings.max_input_file_size_bytes:
            raise InputFileTooLargeError(
                f"The input file is {file_size} bytes; the limit is "
                f"{self.settings.max_input_file_size_bytes} bytes."
            )

        logger.info("[%s] Extraction started for %s", request_id, file_path.name)
        file_bytes = await asyncio.to_thread(file_path.read_bytes)
        content_blocks = await asyncio.to_thread(
            self.parser.to_content_blocks,
            file_bytes,
            mime_type,
        )

        response_text = await asyncio.to_thread(
            self._llm_client().generate_from_blocks,
            system=self._load_prompt("extraction_system.md"),
            user_msg=self._load_prompt("extraction_user.md"),
            content_blocks=content_blocks,
            response_schema=FinancialStatementData.model_json_schema(),
            metadata={"transaction_id": request_id},
        )

        try:
            extracted = FinancialStatementData.model_validate_json(response_text)
        except ValidationError as exc:
            logger.warning("[%s] Invalid LLM response: %s", request_id, exc)
            raise LLMResponseError() from exc

        result = FinancialExtractionResult(
            **extracted.model_dump(),
            quarter=quarter_from_date(extracted.metadata.financial_date_iso),
            reported_date=self.date_provider(),
        )

        if self.settings.save_output:
            await asyncio.to_thread(self._save_result, file_path.stem, result)

        logger.info(
            "[%s] Extraction completed for %s (quarter=%s)",
            request_id,
            file_path.name,
            result.quarter,
        )
        return result

    def resolve_input_path(self, input_path: str) -> Path:
        try:
            relative_path = Path(input_path)
        except (TypeError, ValueError) as exc:
            raise InvalidInputPathError() from exc

        if relative_path.is_absolute():
            raise InvalidInputPathError("Absolute input paths are not allowed.")

        input_root = self.settings.input_directory.resolve()
        try:
            candidate = (input_root / relative_path).resolve()
            candidate.relative_to(input_root)
        except (OSError, ValueError) as exc:
            raise InvalidInputPathError() from exc

        if not candidate.is_file():
            raise InputFileNotFoundError()
        return candidate

    def output_path_for(self, input_path: str) -> Path:
        return self.settings.output_directory / f"{Path(input_path).stem}.json"

    def _load_prompt(self, filename: str) -> str:
        return (self.prompt_dir / filename).read_text(encoding="utf-8")

    def _llm_client(self) -> LLMClient:
        if self.llm is None:
            self.llm = AnthropicLLMClient(self.settings)
        return self.llm

    def _save_result(self, input_stem: str, result: FinancialExtractionResult) -> None:
        output_dir = self.settings.output_directory
        output_path = output_dir / f"{input_stem}.json"
        temporary_path = output_dir / f".{input_stem}.{uuid4().hex}.tmp"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(
                    result.model_dump(mode="json"),
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(output_path)
        except OSError as exc:
            raise OutputWriteError() from exc
        finally:
            temporary_path.unlink(missing_ok=True)
