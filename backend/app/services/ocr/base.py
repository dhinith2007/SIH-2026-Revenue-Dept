from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class OCRExtractedField(BaseModel):
    value: str
    confidence: float = 0.95
    bounding_box: Optional[Dict[str, float]] = None  # { "x": 0.1, "y": 0.2, "width": 0.4, "height": 0.05 }


class OCRRawResult(BaseModel):
    provider: str = "SIMULATED"
    status: str = "SUCCESS"  # SUCCESS, LOW_CONFIDENCE, FAILED, EMPTY
    raw_text: str = ""
    overall_confidence: float = 0.95
    fields: Dict[str, OCRExtractedField] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_simulated: bool = True
    error_message: Optional[str] = None


class BaseOCRProvider(ABC):
    """
    Abstract interface for OCR extraction providers.
    Allows swappable engines (Simulated, Tesseract, EasyOCR, or Cloud Providers in future)
    without modifying Revenue business logic.
    """

    @abstractmethod
    def extract_text(
        self,
        document_data: Optional[bytes] = None,
        filename: str = "document.pdf",
        mime_type: str = "application/pdf",
        context: Optional[Dict[str, Any]] = None,
    ) -> OCRRawResult:
        """
        Extract raw text and structured fields from a document binary or context.
        """
        pass
