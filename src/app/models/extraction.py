from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompanyMetadata(StrictModel):
    company_name: str | None = Field(
        default=None,
        description="Company name as printed in the document",
    )
    financial_date: str | None = Field(
        default=None,
        description="Date associated with the extracted financial statements, as printed",
    )
    financial_date_iso: date | None = Field(
        default=None,
        description=(
            "The same financial_date, normalized to ISO 8601 (YYYY-MM-DD). "
            "Convert Thai Buddhist-era years to Gregorian and Thai month names to their "
            "calendar equivalent. Return null when the printed date cannot be resolved "
            "to a complete date."
        ),
    )


class BalanceSheet(StrictModel):
    cash: float | None = Field(
        default=None,
        description="Unrestricted cash and cash equivalents stated in the balance sheet",
    )
    asset: float | None = Field(
        default=None,
        description="Total assets stated in the balance sheet",
    )
    liabilities: float | None = Field(
        default=None,
        description="Total liabilities stated in the balance sheet",
    )
    equity: float | None = Field(
        default=None,
        description="Total shareholders' equity stated in the balance sheet",
    )


class IncomeStatement(StrictModel):
    revenue: float | None = Field(
        default=None,
        description="Revenue stated in the income statement",
    )
    expense: float | None = Field(
        default=None,
        description="Total expense stated in the income statement",
    )
    operating_profit: float | None = Field(
        default=None,
        description="Operating profit stated in the income statement",
    )
    ebit: float | None = Field(
        default=None,
        description="EBIT directly stated or explicitly labeled as profit before interest and taxes",
    )
    ebitda: float | None = Field(
        default=None,
        description="EBITDA directly stated in the document; never derive it",
    )
    net_profit: float | None = Field(
        default=None,
        description="Net profit or profit for the period stated in the income statement",
    )


class FinancialStatementData(StrictModel):
    """Schema supplied to the LLM; excludes deterministic application fields."""

    metadata: CompanyMetadata = Field(default_factory=CompanyMetadata)
    balance_sheet: BalanceSheet = Field(default_factory=BalanceSheet)
    income_statement: IncomeStatement = Field(default_factory=IncomeStatement)


class FinancialExtractionResult(FinancialStatementData):
    """Stable public response returned by both the API and CLI."""

    quarter: str | None = Field(
        default=None,
        description="Calendar quarter derived from financial_date_iso",
    )
    reported_date: date = Field(
        description="UTC date on which the extraction ran",
    )
