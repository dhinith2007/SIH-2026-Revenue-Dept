import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.services.ocr.base import BaseOCRProvider, OCRRawResult, OCRExtractedField


class SimulatedOCRProvider(BaseOCRProvider):
    """
    Deterministic Simulated AI/OCR Provider for Revenue & Forest Department SIH Demonstration.
    Extracts structured fields with realistic confidence scores, without requiring cloud APIs.
    """

    def extract_text(
        self,
        document_data: Optional[bytes] = None,
        filename: str = "Proof_Document.pdf",
        mime_type: str = "application/pdf",
        context: Optional[Dict[str, Any]] = None,
    ) -> OCRRawResult:
        ctx = context or {}
        app_id = ctx.get("application_id", "")
        doc_dict = ctx.get("document", {})
        new_addr = ctx.get("new_address", {})
        citizen_name = ctx.get("citizen_name", "Rajesh Shantaram Patil")
        forced_status = doc_dict.get("verification_status", "VALIDATED")

        # Check for explicitly invalid or corrupt files
        if forced_status == "INVALID" or "corrupt" in filename.lower():
            return OCRRawResult(
                provider="SIMULATED",
                status="FAILED",
                raw_text="",
                overall_confidence=0.0,
                fields={},
                metadata={"filename": filename, "mime_type": mime_type, "error": "Unreadable document format"},
                is_simulated=True,
                error_message="Document text unreadable or corrupt format.",
            )

        # Check for empty file
        if document_data is not None and len(document_data) == 0:
            return OCRRawResult(
                provider="SIMULATED",
                status="EMPTY",
                raw_text="",
                overall_confidence=0.0,
                fields={},
                metadata={"filename": filename, "mime_type": mime_type},
                is_simulated=True,
                error_message="Empty file provided (0 bytes).",
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

        doc_ref = doc_dict.get("document_id", f"DOC-{app_id.replace('GM-', '') or '9081'}")
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
                value=extracted_name,
                confidence=0.97,
                bounding_box={"x": 0.15, "y": 0.28, "width": 0.45, "height": 0.04},
            ),
            "address": OCRExtractedField(
                value=extracted_addr_str,
                confidence=0.93,
                bounding_box={"x": 0.15, "y": 0.35, "width": 0.70, "height": 0.08},
            ),
            "house_no": OCRExtractedField(value=house_no, confidence=0.91),
            "street": OCRExtractedField(value=street, confidence=0.92),
            "village": OCRExtractedField(value=village, confidence=0.94),
            "taluka": OCRExtractedField(
                value=taluka,
                confidence=0.96,
                bounding_box={"x": 0.15, "y": 0.45, "width": 0.25, "height": 0.04},
            ),
            "district": OCRExtractedField(value=district, confidence=0.98),
            "pincode": OCRExtractedField(
                value=pincode,
                confidence=0.99,
                bounding_box={"x": 0.45, "y": 0.45, "width": 0.20, "height": 0.04},
            ),
            "consumer_number": OCRExtractedField(value=consumer_no, confidence=0.98),
            "issue_date": OCRExtractedField(value=issue_date, confidence=0.95),
            "document_reference": OCRExtractedField(value=doc_ref, confidence=0.99),
        }

        return OCRRawResult(
            provider="SIMULATED",
            status="SUCCESS",
            raw_text=raw_text,
            overall_confidence=0.95,
            fields=fields,
            metadata={
                "filename": filename,
                "mime_type": mime_type,
                "document_id": doc_ref,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            },
            is_simulated=True,
            error_message=None,
        )
