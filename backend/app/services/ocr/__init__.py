from typing import Optional, Dict, Type
from app.core.config import settings
from app.services.ocr.base import BaseOCRProvider, OCRRawResult, OCRExtractedField
from app.services.ocr.simulated_provider import SimulatedOCRProvider
from app.services.ocr.tesseract_provider import LocalTesseractOCRProvider

_PROVIDERS: Dict[str, Type[BaseOCRProvider]] = {
    "SIMULATED": SimulatedOCRProvider,
    "TESSERACT": LocalTesseractOCRProvider,
}


def get_ocr_provider(provider_type: Optional[str] = None) -> BaseOCRProvider:
    """
    Factory to retrieve configured OCR engine.
    - Defaults to settings.OCR_PROVIDER (or "SIMULATED" if unset).
    - Case-insensitive matching.
    - Fails safely with ValueError for unsupported or invalid provider names.
    """
    target = provider_type or getattr(settings, "OCR_PROVIDER", "SIMULATED")
    clean_target = target.strip().upper() if target else "SIMULATED"

    if clean_target not in _PROVIDERS:
        raise ValueError(
            f"Invalid OCR provider '{clean_target}'. Supported providers: {sorted(list(_PROVIDERS.keys()))}"
        )

    cls = _PROVIDERS[clean_target]
    return cls()


__all__ = [
    "BaseOCRProvider",
    "OCRRawResult",
    "OCRExtractedField",
    "SimulatedOCRProvider",
    "LocalTesseractOCRProvider",
    "get_ocr_provider",
]
