import os
import shutil
import subprocess
import tempfile
import time
import hashlib
import re
import unicodedata
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from app.services.ocr.base import BaseOCRProvider, OCRRawResult, OCRExtractedField
from app.services.ocr.normalization import normalize_text, normalize_pincode
from app.core.config import settings
from app.core.logging import logger

COMMON_WINDOWS_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


class LocalTesseractOCRProvider(BaseOCRProvider):
    """
    Production-ready local OCR adapter for Tesseract OCR.
    - Operates completely offline without external cloud dependencies.
    - Bounded execution time via subprocess timeout.
    - Graceful degradation if binary or language packs are missing.
    - Unicode & Devanagari safe.
    - Never leaks internal filesystem paths in error messages.
    """

    def __init__(
        self,
        executable_path: Optional[str] = None,
        languages: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self._custom_cmd = executable_path or settings.TESSERACT_CMD
        self._languages = languages or settings.TESSERACT_LANG or "eng+mar"
        self._timeout = timeout_seconds or settings.OCR_TIMEOUT_SECONDS or 15

    def _resolve_executable(self) -> Optional[str]:
        """Resolves the Tesseract binary path safely."""
        # 1. Custom configured command
        if self._custom_cmd and os.path.exists(self._custom_cmd):
            return self._custom_cmd

        # 2. System PATH
        on_path = shutil.which("tesseract")
        if on_path:
            return on_path

        # 3. Known Windows installations
        if os.name == "nt":
            for p in COMMON_WINDOWS_PATHS:
                if os.path.exists(p):
                    return p

        return None

    def health_check(self) -> Dict[str, Any]:
        """Verifies binary presence and language data availability."""
        cmd = self._resolve_executable()
        if not cmd:
            return {
                "status": "UNAVAILABLE",
                "provider": "TESSERACT",
                "available": False,
                "reason": "Tesseract OCR binary not found on system PATH or configured location.",
            }

        try:
            res = subprocess.run(
                [cmd, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3,
                text=True,
            )
            version_line = res.stdout.splitlines()[0] if res.stdout else "unknown"

            # Check available languages
            langs_res = subprocess.run(
                [cmd, "--list-langs"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3,
                text=True,
            )
            available_langs = [
                ln.strip()
                for ln in langs_res.stdout.splitlines()[1:]
                if ln.strip()
            ]

            return {
                "status": "UP",
                "provider": "TESSERACT",
                "available": True,
                "version": version_line,
                "available_languages": available_langs,
                "configured_languages": self._languages,
            }
        except Exception as exc:
            return {
                "status": "UNAVAILABLE",
                "provider": "TESSERACT",
                "available": False,
                "reason": "Failed to query Tesseract binary readiness.",
            }

    def _resolve_languages(self, cmd: str) -> str:
        """Ensures requested languages exist in tesseract data; falls back safely to 'eng'."""
        try:
            res = subprocess.run(
                [cmd, "--list-langs"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3,
                text=True,
            )
            installed = {
                ln.strip()
                for ln in res.stdout.splitlines()[1:]
                if ln.strip()
            }
            req = [l.strip() for l in self._languages.split("+") if l.strip()]
            valid = [l for l in req if l in installed]
            if valid:
                return "+".join(valid)
            elif "eng" in installed:
                return "eng"
            elif installed:
                return next(iter(installed))
        except Exception:
            pass
        return "eng"

    def extract_text(
        self,
        document_data: Optional[bytes] = None,
        filename: str = "document.pdf",
        mime_type: str = "application/pdf",
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> OCRRawResult:
        start_time = time.perf_counter()
        effective_corr_id = correlation_id or (context or {}).get("correlation_id")

        # 1. Evidence Integrity Hashing
        doc_hash = hashlib.sha256(document_data).hexdigest() if document_data else None

        # 2. Check for empty file
        if document_data is not None and len(document_data) == 0:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return OCRRawResult(
                provider="TESSERACT",
                status="EMPTY",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                error_message="Empty document file provided (0 bytes).",
                error_information={"code": "DOCUMENT_EMPTY"},
                is_simulated=False,
            )

        # 3. Resolve executable
        cmd = self._resolve_executable()
        if not cmd:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return OCRRawResult(
                provider="TESSERACT",
                status="FAILED",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                error_message="Local OCR engine (Tesseract) is unavailable or not installed on this host.",
                error_information={"code": "TESSERACT_NOT_FOUND"},
                is_simulated=False,
            )

        # 4. Check for missing document binary
        if not document_data:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return OCRRawResult(
                provider="TESSERACT",
                status="FAILED",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                error_message="No document binary data supplied for local OCR processing.",
                error_information={"code": "NO_BINARY_DATA"},
                is_simulated=False,
            )

        # 5. Resolve languages
        lang_arg = self._resolve_languages(cmd)

        # 6. Execute OCR via sandboxed temporary file with bounded timeout
        ext = os.path.splitext(filename)[1].lower() or ".pdf"
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(document_data)
                temp_file = f.name

            run_args = [
                cmd,
                temp_file,
                "stdout",
                "-l",
                lang_arg,
                "--oem",
                "1",
            ]

            proc = subprocess.run(
                run_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._timeout,
            )

            if proc.returncode != 0:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return OCRRawResult(
                    provider="TESSERACT",
                    status="FAILED",
                    raw_text="",
                    overall_confidence=0.0,
                    confidence=0.0,
                    fields={},
                    document_hash=doc_hash,
                    correlation_id=effective_corr_id,
                    processing_duration_ms=duration_ms,
                    error_message="Local OCR engine reported an extraction failure on this file.",
                    error_information={"code": "TESSERACT_EXECUTION_ERROR"},
                    is_simulated=False,
                )

            # 7. Unicode extraction & NFC normalization
            raw_text = proc.stdout.decode("utf-8", errors="replace")
            raw_text = unicodedata.normalize("NFC", raw_text)

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if not raw_text.strip():
                return OCRRawResult(
                    provider="TESSERACT",
                    status="EMPTY",
                    raw_text="",
                    overall_confidence=0.0,
                    confidence=0.0,
                    fields={},
                    document_hash=doc_hash,
                    correlation_id=effective_corr_id,
                    processing_duration_ms=duration_ms,
                    error_message="OCR engine executed successfully but detected no readable text.",
                    error_information={"code": "EMPTY_OUTPUT"},
                    is_simulated=False,
                )

            # 8. Field Extraction Heuristics
            fields = self._extract_structured_fields(raw_text)

            # Score confidence based on extraction volume and field detection
            conf = 0.88 if len(fields) >= 2 else (0.75 if len(raw_text.strip()) > 30 else 0.55)
            status = "LOW_CONFIDENCE" if conf < 0.70 else "SUCCESS"

            return OCRRawResult(
                provider="TESSERACT",
                status=status,
                raw_text=raw_text,
                full_text=raw_text,
                overall_confidence=conf,
                confidence=conf,
                fields=fields,
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                metadata={
                    "filename": filename,
                    "mime_type": mime_type,
                    "language": lang_arg,
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                },
                is_simulated=False,
                error_message=None,
            )

        except subprocess.TimeoutExpired:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return OCRRawResult(
                provider="TESSERACT",
                status="FAILED",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                error_message=f"OCR extraction exceeded processing limit ({self._timeout}s).",
                error_information={"code": "OCR_TIMEOUT"},
                is_simulated=False,
            )
        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return OCRRawResult(
                provider="TESSERACT",
                status="FAILED",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                error_message="Unexpected error during local document OCR extraction.",
                error_information={"code": "INTERNAL_OCR_ERROR"},
                is_simulated=False,
            )
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    def _extract_structured_fields(self, raw_text: str) -> Dict[str, OCRExtractedField]:
        """Extracts structured fields from raw OCR text using regex heuristics."""
        fields: Dict[str, OCRExtractedField] = {}

        # 1. Pincode
        pin_match = re.search(r"\b\d{6}\b|[०-९]{6}", raw_text)
        if pin_match:
            normalized_pin = normalize_pincode(pin_match.group(0))
            fields["pincode"] = OCRExtractedField(
                field_name="pincode",
                value=normalized_pin,
                confidence=0.95,
                source="TESSERACT",
            )

        # 2. Taluka
        taluka_match = re.search(r"(?:taluka|तालुका)[\s:\.]*([A-Za-z\u0900-\u097F]+)", raw_text, re.IGNORECASE)
        if taluka_match:
            taluka_val = taluka_match.group(1).strip()
            fields["taluka"] = OCRExtractedField(
                field_name="taluka",
                value=taluka_val,
                confidence=0.90,
                source="TESSERACT",
            )

        # 3. District
        dist_match = re.search(r"(?:district|जिल्हा)[\s:\.]*([A-Za-z\u0900-\u097F]+)", raw_text, re.IGNORECASE)
        if dist_match:
            dist_val = dist_match.group(1).strip()
            fields["district"] = OCRExtractedField(
                field_name="district",
                value=dist_val,
                confidence=0.90,
                source="TESSERACT",
            )

        # 4. Consumer / Document Reference Number
        ref_match = re.search(r"(?:consumer\s*no|ग्राहक\s*क्र|doc(?:ument)?\s*ref)[\s:\.]*([A-Za-z0-9\-]+)", raw_text, re.IGNORECASE)
        if ref_match:
            ref_val = ref_match.group(1).strip()
            fields["consumer_number"] = OCRExtractedField(
                field_name="consumer_number",
                value=ref_val,
                confidence=0.92,
                source="TESSERACT",
            )
            fields["document_number"] = OCRExtractedField(
                field_name="document_number",
                value=ref_val,
                confidence=0.92,
                source="TESSERACT",
            )

        # 5. Issue Date
        date_match = re.search(r"(?:bill\s*date|date|दिनांक)[\s:\.]*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})", raw_text, re.IGNORECASE)
        if date_match:
            date_val = date_match.group(1).strip()
            fields["issue_date"] = OCRExtractedField(
                field_name="issue_date",
                value=date_val,
                confidence=0.88,
                source="TESSERACT",
            )

        return fields
