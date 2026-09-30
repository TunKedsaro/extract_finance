from functools import lru_cache

from ..core.config import get_settings
from ..services.extraction_service import ExtractionService


@lru_cache
def get_extraction_service() -> ExtractionService:
    return ExtractionService(settings=get_settings())
