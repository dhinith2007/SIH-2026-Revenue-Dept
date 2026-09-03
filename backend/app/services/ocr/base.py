from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class OCRExtractedField(BaseModel):
    field_name: Optional[str] = None
    value: str
    confidence: float = 0.95
    bounding_box: Optional[Dict[str, float]] = None  # { "x": 0.1, "y": 0.2, "width": 0.4, "height": 0.05 }
    page_number: Optional[int] = 1
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OCRRawResult(BaseModel):
    provider: str = "SIMULATED"
    status: str = "SUCCESS"  # PENDING, PROCESSING, SUCCESS, FAILED, LOW_CONFIDENCE, EMPTY
    raw_text: str = ""
    full_text: str = ""
    overall_confidence: float = 0.95
    confidence: float = 0.95
    fields: Dict[str, OCRExtractedField] = Field(default_factory=dict)
    processing_duration_ms: float = 0.0
    page_count: int = 1
    document_hash: Optional[str] = None
    correlation_id: Optional[str] = None
    extraction_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    error_information: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_simulated: bool = True

    def model_post_init(self, __context: Any) -> None:
        # Synchronize raw_text and full_text for full backwards and forwards compatibility
        if not self.full_text and self.raw_text:
            self.full_text = self.raw_text
        elif not self.raw_text and self.full_text:
            self.raw_text = self.full_text

        # Synchronize confidence and overall_confidence
        if self.confidence != 0.95 and self.overall_confidence == 0.95:
            self.overall_confidence = self.confidence
        elif self.overall_confidence != 0.95 and self.confidence == 0.95:
            self.confidence = self.overall_confidence

        if self.extraction_timestamp is None:
            self.extraction_timestamp = datetime.now(timezone.utc)


class BaseOCRProvider(ABC):
    """
    Abstract interface for OCR extraction providers.
    Allows swappable engines (Simulated, Tesseract, or future on-prem/cloud providers)
    without modifying Revenue business logic.
    """

    @abstractmethod
    def extract_text(
        self,
        document_data: Optional[bytes] = None,
        filename: str = "document.pdf",
        mime_type: str = "application/pdf",
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> OCRRawResult:
        """
        Extract raw text and structured fields from a document binary or context.
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Verify engine availability, executable readiness, and language packs.
        """
        pass
