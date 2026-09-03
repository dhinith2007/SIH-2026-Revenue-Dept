import re
import time
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.services.ocr.base import BaseOCRProvider, OCRRawResult, OCRExtractedField


class SimulatedOCRProvider(BaseOCRProvider):
    """
    Deterministic Simulated AI/OCR Provider for Revenue & Forest Department SIH Demonstration.
    Extracts structured fields with realistic confidence scores, without requiring cloud APIs.
    """

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "UP",
            "provider": "SIMULATED",
            "available": True,
            "version": "simulated-engine-v1.0",
            "languages": ["eng", "mar"],
        }

    def extract_text(
        self,
        document_data: Optional[bytes] = None,
        filename: str = "Proof_Document.pdf",
        mime_type: str = "application/pdf",
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> OCRRawResult:
        start_time = time.perf_counter()
        ctx = context or {}
        app_id = ctx.get("application_id", "")
        doc_dict = ctx.get("document", {})
        new_addr = ctx.get("new_address", {})
        citizen_name = ctx.get("citizen_name", "Rajesh Shantaram Patil")
        forced_status = doc_dict.get("verification_status", "VALIDATED")
        effective_corr_id = correlation_id or ctx.get("correlation_id") or app_id

        # Compute document SHA-256 hash if binary bytes available
        doc_hash = None
        if document_data:
            doc_hash = hashlib.sha256(document_data).hexdigest()
        elif doc_dict.get("document_hash"):
            doc_hash = doc_dict.get("document_hash")

        # Check for explicitly invalid or corrupt files
        if forced_status == "INVALID" or "corrupt" in filename.lower():
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return OCRRawResult(
                provider="SIMULATED",
                status="FAILED",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                metadata={"filename": filename, "mime_type": mime_type, "error": "Unreadable document format"},
                is_simulated=True,
                error_message="Document text unreadable or corrupt format.",
                error_information={"code": "DOCUMENT_UNREADABLE", "reason": "Corrupt file header or invalid format."},
            )

        # Check for empty file
        if document_data is not None and len(document_data) == 0:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return OCRRawResult(
                provider="SIMULATED",
                status="EMPTY",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                document_hash=doc_hash,
                correlation_id=effective_corr_id,
                processing_duration_ms=duration_ms,
                metadata={"filename": filename, "mime_type": mime_type},
                is_simulated=True,
                error_message="Empty file provided (0 bytes).",
                error_information={"code": "DOCUMENT_EMPTY"},
            )

        # Derive or retrieve extracted name
        extracted_name = doc_dict.get("extracted_name") or citizen_name

        # Derive or retrieve extracted address components
        if doc_dict.get("extracted_address"):
            extracted_addr_str = doc_dict["extracted_address"]
            # Parse components if present in string
            house_no = "402"
            street = "Road"
            village = "Area"
            taluka = "Haveli"
            district = "Pune"
            pincode = "411038"

            # Check if specific demo cases match
            if "Baramati" in extracted_addr_str:
                taluka = "Baramati"
                district = "Pune"
                pincode = "413102"
            elif "Haveli" in extracted_addr_str:
                taluka = "Haveli"
                district = "Pune"
            elif "Maval" in extracted_addr_str:
                taluka = "Maval"
                district = "Pune"
        else:
            house_no = new_addr.get("house_no", "Flat 402, Shivshankar Heights")
            street = new_addr.get("street", "Karve Road")
            village = new_addr.get("village", "Kothrud")
            taluka = new_addr.get("taluka", "Haveli")
            district = new_addr.get("district", "Pune")
            pincode = new_addr.get("pincode", "411038")
            extracted_addr_str = f"{house_no}, {street}, {village}, Taluka: {taluka}, Dist: {district} - {pincode}"

        doc_ref = document_id or doc_dict.get("document_id", f"DOC-{app_id.replace('GM-', '') or '9081'}")
        consumer_no = doc_dict.get("consumer_number", "012345678901")
        issue_date = doc_dict.get("upload_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

        # Build raw text representation
        raw_text = (
            f"MAHARASHTRA STATE ELECTRICITY DISTRIBUTION CO. LTD.\n"
            f"CONSUMER INVOICE & ADDRESS VERIFICATION RECEIPT\n"
            f"Consumer No: {consumer_no} | Bill Date: {issue_date}\n"
            f"Consumer Name: {extracted_name}\n"
            f"Premises Address: {extracted_addr_str}\n"
            f"Taluka: {taluka}, District: {district}, PIN: {pincode}\n"
            f"Tariff: LT-I Residential | Meter Status: NORMAL\n"
            f"Document Ref: {doc_ref}\n"
        )

        # Build structured fields with realistic confidence scores
        fields = {
            "name": OCRExtractedField(
                field_name="name",
                value=extracted_name,
                confidence=0.97,
                bounding_box={"x": 0.15, "y": 0.28, "width": 0.45, "height": 0.04},
                source="SIMULATED",
            ),
            "citizen_name": OCRExtractedField(
                field_name="citizen_name",
                value=extracted_name,
                confidence=0.97,
                source="SIMULATED",
            ),
            "address": OCRExtractedField(
                field_name="address",
                value=extracted_addr_str,
                confidence=0.93,
                bounding_box={"x": 0.15, "y": 0.35, "width": 0.70, "height": 0.08},
                source="SIMULATED",
            ),
            "house_no": OCRExtractedField(field_name="house_no", value=house_no, confidence=0.91, source="SIMULATED"),
            "street": OCRExtractedField(field_name="street", value=street, confidence=0.92, source="SIMULATED"),
            "village": OCRExtractedField(field_name="village", value=village, confidence=0.94, source="SIMULATED"),
            "taluka": OCRExtractedField(
                field_name="taluka",
                value=taluka,
                confidence=0.96,
                bounding_box={"x": 0.15, "y": 0.45, "width": 0.25, "height": 0.04},
                source="SIMULATED",
            ),
            "district": OCRExtractedField(field_name="district", value=district, confidence=0.98, source="SIMULATED"),
            "pincode": OCRExtractedField(
                field_name="pincode",
                value=pincode,
                confidence=0.99,
                bounding_box={"x": 0.45, "y": 0.45, "width": 0.20, "height": 0.04},
                source="SIMULATED",
            ),
            "consumer_number": OCRExtractedField(field_name="consumer_number", value=consumer_no, confidence=0.98, source="SIMULATED"),
            "document_number": OCRExtractedField(field_name="document_number", value=consumer_no, confidence=0.98, source="SIMULATED"),
            "issue_date": OCRExtractedField(field_name="issue_date", value=issue_date, confidence=0.95, source="SIMULATED"),
            "document_reference": OCRExtractedField(field_name="document_reference", value=doc_ref, confidence=0.99, source="SIMULATED"),
        }

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return OCRRawResult(
            provider="SIMULATED",
            status="SUCCESS",
            raw_text=raw_text,
            full_text=raw_text,
            overall_confidence=0.95,
            confidence=0.95,
            fields=fields,
            processing_duration_ms=duration_ms,
            document_hash=doc_hash,
            correlation_id=effective_corr_id,
            metadata={
                "filename": filename,
                "mime_type": mime_type,
                "document_id": doc_ref,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            },
            is_simulated=True,
            error_message=None,
        )
