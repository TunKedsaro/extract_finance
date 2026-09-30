import argparse
import asyncio
import json
import sys

from .core.exceptions import AppError
from .services.extraction_service import ExtractionService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract financial statement data from a PDF or XLSX file."
    )
    parser.add_argument(
        "input_path",
        help="Path relative to INPUT_DIR, for example 'statement.pdf'",
    )
    parser.add_argument(
        "--transaction-id",
        help="Optional identifier included in extraction logs and model metadata",
    )
    return parser


async def _run(input_path: str, transaction_id: str | None) -> int:
    try:
        service = ExtractionService()
        result = await service.extract_from_input(
            input_path,
            transaction_id=transaction_id,
        )
    except AppError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        )
    )
    if service.settings.save_output:
        print(
            f"Saved to {service.output_path_for(input_path)}",
            file=sys.stderr,
        )
    return 0


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(asyncio.run(_run(args.input_path, args.transaction_id)))


if __name__ == "__main__":
    main()
