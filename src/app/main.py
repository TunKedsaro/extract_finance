import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.routes import extraction_router, health_router
from .core.config import get_settings
from .core.exceptions import AppError
from .core.logging import configure_logging
from .models.api import ErrorDetail, ErrorResponse


logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Extract structured financial metrics from PDF and XLSX files.",
    )
    application.include_router(health_router)
    application.include_router(extraction_router)

    @application.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("Application error [%s]: %s", exc.code, exc.message)
        return _error_response(exc.status_code, exc.code, exc.message)

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(item) for item in first_error.get("loc", []))
        detail = first_error.get("msg", "Invalid request payload.")
        message = f"{location}: {detail}" if location else detail
        return _error_response(422, "request_validation_error", message)

    @application.exception_handler(Exception)
    async def handle_unexpected_error(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        return _error_response(
            500,
            "internal_server_error",
            "An unexpected error occurred.",
        )

    return application


app = create_app()
