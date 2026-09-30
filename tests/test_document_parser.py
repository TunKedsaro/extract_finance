import base64
import io
from pathlib import Path

import fitz
import openpyxl
import pytest

from app.core.exceptions import DocumentProcessingError, UnsupportedDocumentTypeError
from app.services.document_parser import (
    MIME_TYPES,
    PDF_MIME_TYPE,
    XLSX_MIME_TYPE,
    DocumentParser,
)


def test_supported_mime_types() -> None:
    parser = DocumentParser()

    assert set(MIME_TYPES) == {".pdf", ".xlsx"}
    assert parser.mime_type_for(Path("REPORT.PDF")) == PDF_MIME_TYPE
    assert parser.mime_type_for(Path("REPORT.XLSX")) == XLSX_MIME_TYPE

    with pytest.raises(UnsupportedDocumentTypeError):
        parser.mime_type_for(Path("report.csv"))


def test_pdf_routes_text_and_image_pages() -> None:
    image_document = fitz.open()
    image_page = image_document.new_page(width=20, height=20)
    image_page.draw_rect(image_page.rect, color=(0, 0, 0), fill=(1, 1, 1))
    png = image_page.get_pixmap().tobytes("png")
    image_document.close()

    pdf = fitz.open()
    text_page = pdf.new_page()
    text_page.insert_textbox(
        fitz.Rect(30, 40, 580, 750),
        "Financial statement page with selectable text. " * 12,
        fontsize=9,
    )
    scan_page = pdf.new_page()
    scan_page.insert_image(scan_page.rect, stream=png)
    mixed_page = pdf.new_page()
    mixed_page.insert_image(mixed_page.rect, stream=png)
    mixed_page.insert_textbox(
        fitz.Rect(30, 40, 580, 750),
        "Selectable text over a full-page scan. " * 12,
        fontsize=9,
    )
    pdf_bytes = pdf.tobytes()
    pdf.close()

    blocks = DocumentParser.pdf_to_content_blocks(pdf_bytes)

    assert [block["type"] for block in blocks] == [
        "text",
        "text",
        "image",
        "text",
        "image",
    ]
    assert "Page 1 (text)" in blocks[0]["text"]
    assert blocks[1]["text"] == "Page 2 image:"
    assert blocks[3]["text"] == "Page 3 image:"
    assert base64.b64decode(blocks[2]["source"]["data"]).startswith(b"\xff\xd8")
    assert base64.b64decode(blocks[4]["source"]["data"]).startswith(b"\xff\xd8")


def test_invalid_pdf_is_reported_as_document_error() -> None:
    with pytest.raises(DocumentProcessingError):
        DocumentParser.pdf_to_content_blocks(b"not a pdf")


def test_xlsx_preserves_sheet_and_column_position() -> None:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Balance Sheet"
    worksheet["A1"] = "Current assets"
    worksheet["B2"] = "Cash"
    worksheet["C2"] = 1250
    buffer = io.BytesIO()
    workbook.save(buffer)
    workbook.close()

    text = DocumentParser.xlsx_to_text(buffer.getvalue())

    assert "=== Sheet: Balance Sheet ===" in text
    assert "Current assets" in text
    assert "  Cash |     1250" in text
