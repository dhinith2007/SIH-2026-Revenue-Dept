from app.services.ocr.base import BaseOCRProvider, OCRRawResult, OCRExtractedField
from app.services.ocr.simulated_provider import SimulatedOCRProvider

_PROVIDERS = {
    "SIMULATED": SimulatedOCRProvider,
}


def get_ocr_provider(provider_type: str = "SIMULATED") -> BaseOCRProvider:
    """
    Factory to retrieve configured OCR engine.
    Defaults to SimulatedOCRProvider for SIH prototype.
    """
    cls = _PROVIDERS.get(provider_type.upper(), SimulatedOCRProvider)
    return cls()
