from datetime import date

from fastapi.testclient import TestClient

from app.api.dependencies import get_extraction_service
from app.core.exceptions import InputFileNotFoundError
from app.main import create_app
from app.models.extraction import FinancialExtractionResult


class FakeExtractionService:
    async def extract_from_input(
        self,
        input_path: str,
        *,
        transaction_id: str | None = None,
    ) -> FinancialExtractionResult:
        assert input_path == "statement.pdf"
        assert transaction_id == "api-test"
        return FinancialExtractionResult(reported_date=date(2026, 9, 30))


class MissingFileService:
    async def extract_from_input(self, *_args, **_kwargs):
        raise InputFileNotFoundError()


def test_health_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_extraction_response_keeps_null_fields() -> None:
    app = create_app()
    app.dependency_overrides[get_extraction_service] = FakeExtractionService

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/extractions",
            json={"input_path": "statement.pdf"},
            headers={"X-Transaction-ID": "api-test"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "metadata": {
            "company_name": None,
            "financial_date": None,
            "financial_date_iso": None,
        },
        "balance_sheet": {
            "cash": None,
            "asset": None,
            "liabilities": None,
            "equity": None,
        },
        "income_statement": {
            "revenue": None,
            "expense": None,
            "operating_profit": None,
            "ebit": None,
            "ebitda": None,
            "net_profit": None,
        },
        "quarter": None,
        "reported_date": "2026-09-30",
    }


def test_application_errors_have_a_stable_shape() -> None:
    app = create_app()
    app.dependency_overrides[get_extraction_service] = MissingFileService

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/extractions",
            json={"input_path": "statement.pdf"},
        )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "input_file_not_found",
            "message": "The requested input file does not exist.",
        }
    }


def test_invalid_payload_has_a_stable_shape() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/extractions",
            json={"input_path": "   "},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"
