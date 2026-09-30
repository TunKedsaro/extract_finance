Extract only the fields in the supplied JSON schema from the financial statement.

## Metadata
- `company_name`: company name as printed in the document.
- `financial_date`: date associated with the current financial statements, as printed. Prefer the balance-sheet date or the end date of the current reporting period. Do not use a comparative-period date.
- `financial_date_iso`: the same date as `financial_date`, converted to ISO 8601 (`YYYY-MM-DD`). Convert Thai Buddhist-era years to Gregorian (Gregorian year = Buddhist year - 543) and Thai month names to their numeric equivalent. This is a format conversion of the printed date, not a guess — return `null` if the printed date is partial (e.g. missing a day) or otherwise cannot be resolved exactly.

## Balance Sheet
Extract only the stated totals for cash, assets, liabilities, and shareholders' equity. Do not calculate a missing total from other figures.
- `cash`: the unrestricted cash and cash equivalents line (e.g. "เงินสดและรายการเทียบเท่าเงินสด" / "Cash and cash equivalents"). Do not include restricted cash, short-term investments, or other near-cash items unless they are part of the same stated line.

## Income Statement
Extract only revenue, total expense, operating profit, EBIT, EBITDA, and net profit.
- Use a directly stated total/primary revenue line. Do not add `Other income` or other lines to it.
- Populate `expense` only when a total expense figure is directly stated. Do not sum individual expense categories.
- Populate EBIT or EBITDA only when a corresponding line is directly stated or clearly labeled with its accounting meaning. Do not derive either from other values.
- Use the document's stated net profit / profit-for-the-period line. Do not substitute profit attributable to parent shareholders unless that is the only net-profit figure stated.

## General Rules
- Read Thai and English statements, including scanned PDFs, text PDFs, and Excel workbooks.
- Preserve the number as reported, including its sign. Parentheses indicate a negative number. Do not convert or scale units.
- If a requested value is not directly stated or is ambiguous, return `null`. Never guess, calculate, or add fields not in the schema.
- Return JSON matching the schema exactly.
