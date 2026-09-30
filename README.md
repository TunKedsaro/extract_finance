# Financial Statement Extraction API

บริการ POC สำหรับดึงข้อมูล Balance Sheet และ Income Statement จากไฟล์ PDF/XLSX
ด้วย Claude รองรับทั้งเอกสารภาษาไทยและอังกฤษ และมีทางเข้าใช้งานสองแบบ:

- FastAPI สำหรับระบบอื่นเรียกผ่าน HTTP
- CLI สำหรับทดสอบหรือรันไฟล์ในเครื่อง

ทั้งสองทางใช้ `ExtractionService` และ parser ชุดเดียวกัน จึงไม่มี extraction logic ซ้ำกัน
ไฟล์ `cli.py` เป็นเพียง command-line entry point ไม่ใช่ parser; parser จริงอยู่ที่
`src/app/services/document_parser.py`

## API contract

ไฟล์ input ต้องอยู่ใต้ `INPUT_DIR` (ค่าเริ่มต้น `resources/input`) และ request ส่ง path
แบบ relative เท่านั้น ระบบไม่อนุญาต absolute path หรือ path ที่ออกนอก input directory

```http
POST /api/v1/extractions
Content-Type: application/json

{
  "input_path": "PTT Financial Statement - Q1 2026.XLSX"
}
```

Response มี schema คงที่ โดย field ที่หาไม่พบจะเป็น `null`:

```json
{
  "metadata": {
    "company_name": "PTT PUBLIC COMPANY LIMITED AND ITS SUBSIDIARIES",
    "financial_date": "31 March 2026",
    "financial_date_iso": "2026-03-31"
  },
  "balance_sheet": {
    "cash": 425431356167.0,
    "asset": 3583215959493.0,
    "liabilities": 1844504686806.0,
    "equity": 1738711272687.0
  },
  "income_statement": {
    "revenue": 718729054591.0,
    "expense": null,
    "operating_profit": 71680025085.0,
    "ebit": 73733839583.0,
    "ebitda": null,
    "net_profit": 41623449904.0
  },
  "quarter": "Q1 2026",
  "reported_date": "2026-09-30"
}
```

`quarter` คำนวณจาก `financial_date_iso` และ `reported_date` ใช้วันที่ UTC ที่รันงาน
สอง field นี้ไม่ได้ให้ LLM สร้างเอง

## ติดตั้งและตั้งค่า

ต้องใช้ Python 3.12 ขึ้นไป

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

ตั้งค่า `.env` ด้วย Terrax token โดยตรง หรือ LiteLLM proxy อย่างใดอย่างหนึ่ง
ห้าม commit `.env` หรือ token จริง

วาง PDF/XLSX ไว้ใน `resources/input/` แล้วเริ่ม API:

```bash
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

ตรวจ health และเรียก extraction:

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/api/v1/extractions \
  -H 'Content-Type: application/json' \
  -H 'X-Transaction-ID: poc-001' \
  -d '{"input_path":"PTT Financial Statement - Q1 2026.XLSX"}'
```

Swagger UI อยู่ที่ <http://localhost:8000/docs>

## CLI

เรียกจาก project root และส่ง path ที่ relative กับ `INPUT_DIR`:

```bash
python -m src.app.cli "PTT Financial Statement - Q1 2026.XLSX"
```

CLI แสดง JSON ทาง stdout และบันทึกไฟล์เช่นเดียวกับ API เมื่อ `SAVE_OUTPUT=true`

## การบันทึกผล

ค่าเริ่มต้นจะคืน JSON และบันทึก `outputs/<ชื่อ input>.json` ด้วย หากต้องการคืน response
อย่างเดียวให้ตั้ง:

```env
SAVE_OUTPUT=false
```

## Docker Compose

```bash
docker compose up --build
```

Compose mount `resources/input` แบบ read-only และ `outputs` แบบ read-write

## Tests

ชุดทดสอบไม่เรียก LLM จริง:

```bash
pytest
```

รายละเอียดโครงสร้างดูที่ [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
และรายละเอียด endpoint ดูที่ [docs/API.md](docs/API.md)
