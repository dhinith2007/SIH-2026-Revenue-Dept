from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import hashlib
from app.schemas.workflow import DocumentVerificationResult, DocumentExtractedFields
from app.services.ocr import get_ocr_provider
from app.services.ocr.base import OCRRawResult
from app.services.ocr.matcher import (
    compare_name,
    compare_address_components,
    compute_assistive_score,
    generate_verification_explanation,
)
from app.services.ocr.confidence_engine import RuleBasedVerificationConfidenceEngine
from app.repositories.document_evidence_repository import DocumentEvidenceRepository
from app.core.config import settings
from app.core.logging import logger


class DocumentVerificationService:
    """
    Advanced Document Verification & OCR Assistance Service.
    Coordinates swappable OCR extraction, field normalization, component matching,
    rule-based AI confidence evaluation, SHA-256 evidence integrity, relational persistence,
    and explainability generation for Revenue Officers.
    """

    @classmethod
    def verify_document(
        cls,
        app_dict: Dict[str, Any],
        doc_index: int = 0,
        provider_type: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> DocumentVerificationResult:
        """
        Verifies a specific proof document attached to an application using configured OCR provider.
        """
        effective_provider = (
            provider_type.upper() if provider_type else getattr(settings, "OCR_PROVIDER", "SIMULATED").upper()
        )
        app_id = app_dict.get("application_id", "")
        data_payload = app_dict.get("data_payload", {})
        new_addr = data_payload.get("new_address", {})
        citizen_name = app_dict.get("citizen_name", "").strip()
        proof_docs = data_payload.get("proof_documents", [])
        corr_id = app_dict.get("correlation_id", app_id)

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
                provider=effective_provider,
                is_simulated_ocr=(effective_provider == "SIMULATED"),
                document_hash=None,
                processing_duration_ms=0.0,
                verification_timestamp=datetime.now(timezone.utc),
                ocr_confidence=0.0,
                match_confidence=0.0,
                overall_confidence=0.0,
                recommendation="INSUFFICIENT_EVIDENCE",
                evidence_quality="INSUFFICIENT",
                risk_flags=["MISSING_CRITICAL_FIELD"],
                reasons=[explanation],
                officer_guidance=explanation,
            )

        doc = proof_docs[doc_index]
        doc_id = doc.get("document_id", "DOC-UNKNOWN")
        doc_name = doc.get("document_name", "Proof_Document.pdf")
        doc_type = doc.get("document_type", "ELECTRICITY_BILL")
        forced_status = doc.get("verification_status", "PENDING")
        doc_content = doc.get("content")  # bytes if uploaded in-memory

        # 1. OCR Extraction Layer (with safe provider resolution)
        try:
            ocr_engine = get_ocr_provider(effective_provider)
            ocr_raw = ocr_engine.extract_text(
                document_data=doc_content,
                filename=doc_name,
                mime_type=doc.get("mime_type", "application/pdf"),
                context={
                    "application_id": app_id,
                    "document": doc,
                    "new_address": new_addr,
                    "citizen_name": citizen_name,
                    "correlation_id": corr_id,
                },
                correlation_id=corr_id,
                document_id=doc_id,
            )
        except ValueError as val_err:
            # Handle invalid provider configuration gracefully without crashing or approving
            ocr_raw = OCRRawResult(
                provider=effective_provider,
                status="FAILED",
                raw_text="",
                overall_confidence=0.0,
                confidence=0.0,
                fields={},
                error_message=f"Invalid OCR provider configured: {val_err}",
                error_information={"code": "INVALID_PROVIDER"},
                is_simulated=False,
            )

        # Retrieve or compute SHA-256 hash
        doc_hash = ocr_raw.document_hash or doc.get("document_hash")
        duration_ms = ocr_raw.processing_duration_ms

        # 2. Check for OCR Extraction failure or corrupt document
        if ocr_raw.status in ("FAILED", "EMPTY") or forced_status == "INVALID":
            explanation = ocr_raw.error_message or "Supporting document is corrupt, unreadable, or in an unsupported format."
            result = DocumentVerificationResult(
                document_id=doc_id,
                document_name=doc_name,
                document_type=doc_type,
                valid=False,
                match_status="INVALID" if ocr_raw.status != "EMPTY" else "EMPTY",
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
                provider=ocr_raw.provider,
                is_simulated_ocr=(ocr_raw.provider == "SIMULATED"),
                document_hash=doc_hash,
                processing_duration_ms=duration_ms,
                verification_timestamp=datetime.now(timezone.utc),
                ocr_confidence=0.0,
                match_confidence=0.0,
                overall_confidence=0.0,
                recommendation="INSUFFICIENT_EVIDENCE",
                evidence_quality="FAILED",
                risk_flags=["OCR_FAILED"],
                reasons=[explanation],
                officer_guidance="Document binary could not be processed by OCR engine. Request fresh document scan from citizen.",
            )

            # Persist failure evidence record
            evidence_repo = DocumentEvidenceRepository(db=db)
            evidence_repo.save_evidence({
                "document_id": doc_id,
                "application_id": app_id,
                "document_hash": doc_hash,
                "provider": ocr_raw.provider,
                "status": "FAILED",
                "confidence": 0.0,
                "extracted_fields": {},
                "field_confidences": {"overall": 0.0},
                "error_message": explanation,
                "processing_duration_ms": duration_ms,
                "correlation_id": corr_id,
            })

            return result

        # 3. Field Normalization & Component Matching
        extracted_name = (
            ocr_raw.fields.get("name").value
            if ocr_raw.fields.get("name")
            else (doc.get("extracted_name") or citizen_name)
        )
        extracted_addr_str = (
            ocr_raw.fields.get("address").value
            if ocr_raw.fields.get("address")
            else (doc.get("extracted_address") or "")
        )

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

        # Phase 10 Step 04: Confidence Engine Evaluation
        conf_engine = RuleBasedVerificationConfidenceEngine()
        conf_res = conf_engine.evaluate_confidence(
            ocr_raw=ocr_raw,
            name_eval=name_eval,
            comp_eval=comp_eval,
            assistive_score=assist_score,
            context={"application_id": app_id, "document_id": doc_id},
        )

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
        has_pincode_mismatch = comp_eval.get("pincode", {}).get("result") == "MISMATCH"
        has_any_mismatch = (
            any(c.get("result") == "MISMATCH" for c in comp_eval.values())
            or has_name_mismatch
        )
        has_any_partial = (
            any(c.get("result") == "PARTIAL_MATCH" for c in comp_eval.values())
            or (name_eval["result"] == "PARTIAL_MATCH")
        )

        if forced_status == "VALIDATED":
            match_status = "VALIDATED"
            is_valid = True
            address_match = "MATCH"
        elif (
            forced_status in ("REJECTED", "MISMATCH")
            or has_taluka_mismatch
            or has_district_mismatch
            or has_pincode_mismatch
            or has_name_mismatch
        ):
            match_status = "MISMATCH"
            is_valid = False
            address_match = (
                "MISMATCH"
                if (has_taluka_mismatch or has_district_mismatch or has_pincode_mismatch)
                else "PARTIAL_MATCH"
            )
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
            citizen_name=extracted_name,
            house_no=extracted_comp_dict.get("house_no"),
            street=extracted_comp_dict.get("street"),
            village=extracted_comp_dict.get("village"),
            taluka=extracted_comp_dict.get("taluka"),
            district=extracted_comp_dict.get("district"),
            pincode=extracted_comp_dict.get("pincode"),
            consumer_number=ocr_raw.fields.get("consumer_number").value if ocr_raw.fields.get("consumer_number") else None,
            document_number=ocr_raw.fields.get("consumer_number").value if ocr_raw.fields.get("consumer_number") else None,
            issue_date=ocr_raw.fields.get("issue_date").value if ocr_raw.fields.get("issue_date") else doc.get("upload_date"),
            document_type=doc_type,
            document_reference=doc_id,
            raw_text=ocr_raw.raw_text,
        )

        # Log metadata only (DPDP compliance: no raw text, no citizen PII logged)
        logger.info(
            "Document Verification: app_id='%s' (doc: %s): provider=%s, status=%s, assist_score=%.2f, rec=%s, overall_conf=%.2f, hash=%s, valid=%s",
            app_id,
            doc_id,
            ocr_raw.provider,
            match_status,
            assist_score,
            conf_res.recommendation,
            conf_res.overall_confidence,
            doc_hash,
            is_valid,
        )

        # 7. Persist Relational Evidence Record
        evidence_repo = DocumentEvidenceRepository(db=db)
        evidence_repo.save_evidence({
            "document_id": doc_id,
            "application_id": app_id,
            "document_hash": doc_hash,
            "provider": ocr_raw.provider,
            "status": match_status,
            "confidence": conf_res.overall_confidence,
            "extracted_fields": {k: v.value for k, v in ocr_raw.fields.items()},
            "field_confidences": field_confidences,
            "error_message": None,
            "processing_duration_ms": duration_ms,
            "correlation_id": corr_id,
        })

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
            provider=ocr_raw.provider,
            is_simulated_ocr=(ocr_raw.provider == "SIMULATED"),
            document_hash=doc_hash,
            processing_duration_ms=duration_ms,
            verification_timestamp=datetime.now(timezone.utc),
            manual_override=doc.get("manual_override"),
            # Phase 10 Step 04 Confidence Engine fields
            ocr_confidence=conf_res.ocr_confidence,
            match_confidence=conf_res.match_confidence,
            overall_confidence=conf_res.overall_confidence,
            recommendation=conf_res.recommendation,
            evidence_quality=conf_res.evidence_quality,
            risk_flags=conf_res.risk_flags,
            reasons=conf_res.reasons,
            officer_guidance=conf_res.officer_guidance,
            score_breakdown=conf_res.score_breakdown,
        )

    @classmethod
    def verify_all_documents(
        cls,
        app_dict: Dict[str, Any],
        provider_type: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> List[DocumentVerificationResult]:
        """
        Batch-verifies all proof documents attached to an application.
        """
        data_payload = app_dict.get("data_payload", {})
        proof_docs = data_payload.get("proof_documents", [])
        if not proof_docs:
            return [cls.verify_document(app_dict, doc_index=0, provider_type=provider_type, db=db)]

        results = []
        for idx in range(len(proof_docs)):
            results.append(cls.verify_document(app_dict, doc_index=idx, provider_type=provider_type, db=db))
        return results
