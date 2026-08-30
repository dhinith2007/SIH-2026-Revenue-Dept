from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from app.schemas.workflow import DocumentVerificationResult, DocumentExtractedFields
from app.services.ocr import get_ocr_provider
from app.services.ocr.matcher import (
    compare_name,
    compare_address_components,
    compute_assistive_score,
    generate_verification_explanation,
)
from app.core.logging import logger


class DocumentVerificationService:
    """
    Advanced Document Verification & OCR Assistance Service.
    Coordinates swappable OCR extraction, field normalization, component matching,
    confidence evaluation, and explainability generation for Revenue Officers.
    """

    @classmethod
    def verify_document(
        cls,
        app_dict: Dict[str, Any],
        doc_index: int = 0,
        provider_type: str = "SIMULATED",
    ) -> DocumentVerificationResult:
        """
        Verifies a specific proof document attached to an application using configured OCR provider.
        """
        app_id = app_dict.get("application_id", "")
        data_payload = app_dict.get("data_payload", {})
        new_addr = data_payload.get("new_address", {})
        citizen_name = app_dict.get("citizen_name", "").strip()
        proof_docs = data_payload.get("proof_documents", [])

        if not proof_docs or len(proof_docs) <= doc_index:
            explanation = "No supporting proof documents attached to application. Officer action required to request document from citizen."
            return DocumentVerificationResult(
                document_id="DOC-NONE",
                document_name="No Document Uploaded",
                document_type="MISSING",
                valid=False,
                match_status="MISSING",
                name_match="NOT_EXTRACTED",
                address_match="NOT_EXTRACTED",
                extracted_fields=DocumentExtractedFields(
                    extracted_name="N/A",
                    extracted_address="N/A",
                    document_type="MISSING",
                    document_reference="N/A",
                ),
                field_confidences={},
                component_matches={},
                assistive_score=0.0,
                matched_components_count=0,
                total_components_count=7,
                explanation=explanation,
                details=explanation,
                provider=provider_type,
                is_simulated_ocr=(provider_type == "SIMULATED"),
                verification_timestamp=datetime.now(timezone.utc),
            )

        doc = proof_docs[doc_index]
        doc_id = doc.get("document_id", "DOC-UNKNOWN")
        doc_name = doc.get("document_name", "Proof_Document.pdf")
        doc_type = doc.get("document_type", "ELECTRICITY_BILL")
        forced_status = doc.get("verification_status", "PENDING")

        # 1. OCR Extraction Layer
        ocr_engine = get_ocr_provider(provider_type)
        ocr_raw = ocr_engine.extract_text(
            filename=doc_name,
            mime_type=doc.get("mime_type", "application/pdf"),
            context={
                "application_id": app_id,
                "document": doc,
                "new_address": new_addr,
                "citizen_name": citizen_name,
            },
        )

        # 2. Check for OCR Extraction failure or corrupt document
        if ocr_raw.status == "FAILED" or forced_status == "INVALID":
            explanation = "Supporting document is corrupt, unreadable, or in an unsupported format."
            return DocumentVerificationResult(
                document_id=doc_id,
                document_name=doc_name,
                document_type=doc_type,
                valid=False,
                match_status="INVALID",
                name_match="NOT_EXTRACTED",
                address_match="NOT_EXTRACTED",
                extracted_fields=DocumentExtractedFields(
                    extracted_name="N/A",
                    extracted_address="N/A",
                    document_type=doc_type,
                    document_reference=doc_id,
                    raw_text=ocr_raw.raw_text,
                ),
                field_confidences={"overall": 0.0},
                component_matches={},
                assistive_score=0.0,
                matched_components_count=0,
                total_components_count=7,
                explanation=explanation,
                details=explanation,
                provider=provider_type,
                is_simulated_ocr=(provider_type == "SIMULATED"),
                verification_timestamp=datetime.now(timezone.utc),
            )

        # 3. Field Normalization & Component Matching
        extracted_name = ocr_raw.fields.get("name").value if ocr_raw.fields.get("name") else (doc.get("extracted_name") or citizen_name)
        extracted_addr_str = ocr_raw.fields.get("address").value if ocr_raw.fields.get("address") else (doc.get("extracted_address") or "")

        # Extract structured address components from OCR result
        extracted_comp_dict = {
            "house_no": ocr_raw.fields.get("house_no").value if ocr_raw.fields.get("house_no") else "",
            "street": ocr_raw.fields.get("street").value if ocr_raw.fields.get("street") else "",
            "village": ocr_raw.fields.get("village").value if ocr_raw.fields.get("village") else "",
            "taluka": ocr_raw.fields.get("taluka").value if ocr_raw.fields.get("taluka") else "",
            "district": ocr_raw.fields.get("district").value if ocr_raw.fields.get("district") else "",
            "pincode": ocr_raw.fields.get("pincode").value if ocr_raw.fields.get("pincode") else "",
        }

        # Compare citizen name
        name_eval = compare_name(citizen_name, extracted_name)
        # Compare 6-part address components
        comp_eval = compare_address_components(new_addr, extracted_comp_dict, ocr_raw.raw_text)

        # 4. Confidence Evaluation & Assistive Score
        assist_score, matched_count, total_count = compute_assistive_score(name_eval, comp_eval)

        field_confidences = {
            "overall": ocr_raw.overall_confidence,
            "name": ocr_raw.fields.get("name").confidence if ocr_raw.fields.get("name") else 0.95,
            "address": ocr_raw.fields.get("address").confidence if ocr_raw.fields.get("address") else 0.90,
            "taluka": ocr_raw.fields.get("taluka").confidence if ocr_raw.fields.get("taluka") else 0.95,
            "pincode": ocr_raw.fields.get("pincode").confidence if ocr_raw.fields.get("pincode") else 0.99,
        }

        # 5. Overall Match Status Determination
        has_name_mismatch = name_eval["result"] == "MISMATCH"
        has_taluka_mismatch = comp_eval.get("taluka", {}).get("result") == "MISMATCH"
        has_district_mismatch = comp_eval.get("district", {}).get("result") == "MISMATCH"
        has_any_mismatch = any(c.get("result") == "MISMATCH" for c in comp_eval.values()) or has_name_mismatch
        has_any_partial = any(c.get("result") == "PARTIAL_MATCH" for c in comp_eval.values()) or (name_eval["result"] == "PARTIAL_MATCH")

        if forced_status in ("REJECTED", "MISMATCH") or has_taluka_mismatch or has_district_mismatch or has_name_mismatch:
            match_status = "MISMATCH"
            is_valid = False
            address_match = "MISMATCH" if (has_taluka_mismatch or has_district_mismatch) else "PARTIAL_MATCH"
        elif has_any_mismatch or has_any_partial or assist_score < 0.85:
            match_status = "PARTIAL_MATCH"
            is_valid = False
            address_match = "PARTIAL_MATCH"
        elif ocr_raw.overall_confidence < 0.70:
            match_status = "LOW_CONFIDENCE"
            is_valid = False
            address_match = "PARTIAL_MATCH"
        else:
            match_status = "VALIDATED"
            is_valid = True
            address_match = "MATCH"

        name_match_status = name_eval["result"]

        # 6. Generate Explainable Rationale
        explanation = generate_verification_explanation(name_eval, comp_eval, match_status)

        # Build structured extracted fields model
        extracted_fields = DocumentExtractedFields(
            extracted_name=extracted_name,
            extracted_address=extracted_addr_str,
            house_no=extracted_comp_dict.get("house_no"),
            street=extracted_comp_dict.get("street"),
            village=extracted_comp_dict.get("village"),
            taluka=extracted_comp_dict.get("taluka"),
            district=extracted_comp_dict.get("district"),
            pincode=extracted_comp_dict.get("pincode"),
            consumer_number=ocr_raw.fields.get("consumer_number").value if ocr_raw.fields.get("consumer_number") else None,
            issue_date=ocr_raw.fields.get("issue_date").value if ocr_raw.fields.get("issue_date") else doc.get("upload_date"),
            document_type=doc_type,
            document_reference=doc_id,
            raw_text=ocr_raw.raw_text,
        )

        logger.info(
            "Phase 06 Document Verification for app '%s' (doc: %s): status=%s, assist_score=%.2f (%d/%d), valid=%s",
            app_id,
            doc_id,
            match_status,
            assist_score,
            matched_count,
            total_count,
            is_valid,
        )

        return DocumentVerificationResult(
            document_id=doc_id,
            document_name=doc_name,
            document_type=doc_type,
            valid=is_valid,
            match_status=match_status,
            name_match=name_match_status,
            address_match=address_match,
            extracted_fields=extracted_fields,
            field_confidences=field_confidences,
            component_matches=comp_eval,
            assistive_score=assist_score,
            matched_components_count=matched_count,
            total_components_count=total_count,
            explanation=explanation,
            details=explanation,
            provider=provider_type,
            is_simulated_ocr=(provider_type == "SIMULATED"),
            verification_timestamp=datetime.now(timezone.utc),
            manual_override=doc.get("manual_override"),
        )

    @classmethod
    def verify_all_documents(
        cls,
        app_dict: Dict[str, Any],
        provider_type: str = "SIMULATED",
    ) -> List[DocumentVerificationResult]:
        """
        Batch-verifies all proof documents attached to an application.
        """
        data_payload = app_dict.get("data_payload", {})
        proof_docs = data_payload.get("proof_documents", [])
        if not proof_docs:
            return [cls.verify_document(app_dict, doc_index=0, provider_type=provider_type)]

        results = []
        for idx in range(len(proof_docs)):
            results.append(cls.verify_document(app_dict, doc_index=idx, provider_type=provider_type))
        return results
