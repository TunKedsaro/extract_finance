from typing import Annotated

from fastapi import APIRouter, Depends, Header

from ...models.api import ErrorResponse, ExtractionRequest
from ...models.extraction import FinancialExtractionResult
from ...services.extraction_service import ExtractionService
from ..dependencies import get_extraction_service


router = APIRouter(prefix="/api/v1/extractions", tags=["extractions"])


@router.post(
    "",
    response_model=FinancialExtractionResult,
    response_model_exclude_none=False,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def extract_financial_statement(
    payload: ExtractionRequest,
    service: ExtractionService = Depends(get_extraction_service),
    transaction_id: Annotated[
        str | None,
        Header(alias="X-Transaction-ID", max_length=128),
    ] = None,
) -> FinancialExtractionResult:
    return await service.extract_from_input(
        payload.input_path,
        transaction_id=transaction_id,
    )
