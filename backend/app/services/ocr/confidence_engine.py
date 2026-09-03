import math
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.services.ocr.base import OCRRawResult


class VerificationConfidenceResult(BaseModel):
    ocr_confidence: float = Field(..., ge=0.0, le=1.0, description="OCR provider extraction confidence")
    match_confidence: float = Field(..., ge=0.0, le=1.0, description="Data comparison similarity score")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Weighted evidence confidence score")
    recommendation: str = Field(
        ...,
        description="HIGH_CONFIDENCE_MATCH | MEDIUM_CONFIDENCE_REVIEW | LOW_CONFIDENCE_REVIEW | MISMATCH_REVIEW | INSUFFICIENT_EVIDENCE",
    )
    evidence_quality: str = Field(..., description="COMPLETE | PARTIAL | INSUFFICIENT | FAILED")
    risk_flags: List[str] = Field(default_factory=list, description="List of detected risk indicators")
    reasons: List[str] = Field(default_factory=list, description="Human-readable decision rationales")
    officer_guidance: str = Field(..., description="Statutory guidance note for Revenue Officer")
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Component score weight breakdown")


class BaseVerificationConfidenceEngine(ABC):
    """
    Abstract interface for verification confidence engines.
    Provides clean abstraction allowing rule-based or future ML/AI providers
    to evaluate document evidence without mutating statutory application state.
    """

    @abstractmethod
    def evaluate_confidence(
        self,
        ocr_raw: OCRRawResult,
        name_eval: Dict[str, Any],
        comp_eval: Dict[str, Dict[str, Any]],
        assistive_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationConfidenceResult:
        """Evaluates evidence signals and returns confidence metrics and officer guidance."""
        pass


class RuleBasedVerificationConfidenceEngine(BaseVerificationConfidenceEngine):
    """
    Deterministic rule-based confidence engine for revenue document verification.
    Combines OCR extraction quality, field comparison results, critical field signals,
    and risk overrides to produce explainable officer guidance.
    Operates strictly offline without external LLM/Cloud dependencies.
    """

    def evaluate_confidence(
        self,
        ocr_raw: OCRRawResult,
        name_eval: Dict[str, Any],
        comp_eval: Dict[str, Dict[str, Any]],
        assistive_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationConfidenceResult:
        # Sanitize input floats against NaN, Infinity, negative, or invalid types
        try:
            raw_ocr = float(ocr_raw.overall_confidence) if ocr_raw and ocr_raw.overall_confidence is not None else 0.0
            if math.isnan(raw_ocr) or math.isinf(raw_ocr):
                raw_ocr = 0.0
        except (TypeError, ValueError):
            raw_ocr = 0.0

        try:
            raw_match = float(assistive_score) if assistive_score is not None else 0.0
            if math.isnan(raw_match) or math.isinf(raw_match):
                raw_match = 0.0
        except (TypeError, ValueError):
            raw_match = 0.0

        ocr_conf = round(max(0.0, min(1.0, raw_ocr)), 2)
        match_conf = round(max(0.0, min(1.0, raw_match)), 2)

        # 1. OCR Extraction Failure or Unreadable Document
        if ocr_raw.status in ("FAILED", "EMPTY") or ocr_raw.overall_confidence == 0.0:
            reasons = ["OCR extraction failed or document binary was unreadable."]
            if ocr_raw.error_message:
                reasons.append(ocr_raw.error_message)

            return VerificationConfidenceResult(
                ocr_confidence=0.0,
                match_confidence=0.0,
                overall_confidence=0.0,
                recommendation="INSUFFICIENT_EVIDENCE",
                evidence_quality="FAILED",
                risk_flags=["OCR_FAILED"],
                reasons=reasons,
                officer_guidance="Document binary could not be processed by OCR engine. Request fresh document scan from citizen.",
                score_breakdown={"ocr_quality": 0.0, "match_confidence": 0.0},
            )

        # 2. Risk Flag & Critical Field Analysis
        risk_flags: List[str] = []
        reasons: List[str] = []

        if ocr_conf < 0.75:
            risk_flags.append("OCR_LOW_CONFIDENCE")
            reasons.append(f"OCR provider extraction confidence is below standard threshold ({round(ocr_conf*100)}%).")

        name_status = name_eval.get("result", "NOT_EXTRACTED")
        if name_status == "MISMATCH":
            risk_flags.append("NAME_MISMATCH")
            reasons.append(f"Citizen Name discrepancy detected (Document: '{name_eval.get('document_value')}', Requested: '{name_eval.get('application_value')}').")
        elif name_status == "PARTIAL_MATCH":
            if name_eval.get("method") == "script_difference":
                risk_flags.append("SCRIPT_DIFFERENCE")
                reasons.append("Script difference detected between English application name and Devanagari document name.")
            else:
                risk_flags.append("NAME_PARTIAL_MATCH")
                reasons.append("Citizen Name partially matched.")
        elif name_status in ("NOT_EXTRACTED", "UNAVAILABLE"):
            risk_flags.append("MISSING_CRITICAL_FIELD")
            reasons.append("Citizen Name was not extracted from document.")

        # Address Component Risk Flags
        pincode_status = comp_eval.get("pincode", {}).get("result", "NOT_EXTRACTED")
        district_status = comp_eval.get("district", {}).get("result", "NOT_EXTRACTED")
        taluka_status = comp_eval.get("taluka", {}).get("result", "NOT_EXTRACTED")
        village_status = comp_eval.get("village", {}).get("result", "NOT_EXTRACTED")

        if pincode_status == "MISMATCH":
            risk_flags.append("PINCODE_MISMATCH")
            reasons.append(f"PIN code mismatch: {comp_eval['pincode'].get('explanation')}")
        elif pincode_status in ("NOT_EXTRACTED", "UNAVAILABLE"):
            if "MISSING_CRITICAL_FIELD" not in risk_flags:
                risk_flags.append("MISSING_CRITICAL_FIELD")
            reasons.append("PIN code was not extracted from document.")

        if district_status == "MISMATCH":
            risk_flags.append("DISTRICT_MISMATCH")
            reasons.append(f"District jurisdiction mismatch: {comp_eval['district'].get('explanation')}")

        if taluka_status == "MISMATCH":
            risk_flags.append("TALUKA_MISMATCH")
            reasons.append(f"Taluka jurisdiction mismatch: {comp_eval['taluka'].get('explanation')}")

        if village_status == "MISMATCH":
            risk_flags.append("VILLAGE_MISMATCH")
            reasons.append(f"Village mismatch: {comp_eval['village'].get('explanation')}")

        # 3. Evidence Quality Determination
        extracted_critical_count = sum(
            1 for st in [name_status, pincode_status, district_status, taluka_status]
            if st in ("MATCH", "PARTIAL_MATCH", "MISMATCH")
        )

        if extracted_critical_count >= 4:
            evidence_quality = "COMPLETE"
        elif extracted_critical_count >= 2:
            evidence_quality = "PARTIAL"
        else:
            evidence_quality = "INSUFFICIENT"

        if evidence_quality == "INSUFFICIENT" and "MISSING_CRITICAL_FIELD" not in risk_flags:
            risk_flags.append("MISSING_CRITICAL_FIELD")

        # 4. Critical Field Override Rules
        has_critical_mismatch = (
            pincode_status == "MISMATCH"
            or district_status == "MISMATCH"
            or taluka_status == "MISMATCH"
            or name_status == "MISMATCH"
        )

        if has_critical_mismatch:
            overall_conf = round(min(0.40, match_conf), 2)
            recommendation = "MISMATCH_REVIEW"
            officer_guidance = (
                "Critical discrepancy detected in supporting document evidence. "
                "Carefully verify physical proof document before taking statutory action."
            )
            score_breakdown = {
                "ocr_quality": ocr_conf,
                "match_confidence": match_conf,
                "critical_penalty": 0.60,
                "overall_score": overall_conf,
            }
            return VerificationConfidenceResult(
                ocr_confidence=ocr_conf,
                match_confidence=match_conf,
                overall_confidence=overall_conf,
                recommendation=recommendation,
                evidence_quality=evidence_quality,
                risk_flags=risk_flags,
                reasons=reasons,
                officer_guidance=officer_guidance,
                score_breakdown=score_breakdown,
            )

        # 5. Weighted Overall Confidence Calculation
        weighted_score = round(0.35 * ocr_conf + 0.65 * match_conf, 2)
        if ocr_conf < 0.70:
            weighted_score = round(min(weighted_score, 0.72), 2)

        overall_conf = weighted_score

        # 6. Recommendation Band Classification
        if (
            overall_conf >= 0.85
            and ocr_conf >= 0.75
            and name_status == "MATCH"
            and pincode_status in ("MATCH", "implicit_match")
            and evidence_quality == "COMPLETE"
            and not risk_flags
        ):
            recommendation = "HIGH_CONFIDENCE_MATCH"
            reasons.append("Citizen name, PIN code, and jurisdiction components match document evidence cleanly.")
            officer_guidance = (
                "Document evidence is highly consistent with application details. "
                "Proceed with standard officer statutory review."
            )
        elif overall_conf >= 0.70 and evidence_quality in ("COMPLETE", "PARTIAL"):
            recommendation = "MEDIUM_CONFIDENCE_REVIEW"
            if not reasons:
                reasons.append("Document evidence is generally consistent with minor formatting or confidence variations.")
            officer_guidance = (
                "Document evidence is generally consistent, but minor formatting, script, or confidence differences exist. "
                "Officer review required before approval."
            )
        elif evidence_quality == "INSUFFICIENT" or name_status in ("NOT_EXTRACTED", "UNAVAILABLE"):
            recommendation = "INSUFFICIENT_EVIDENCE"
            reasons.append("Essential proof fields were not extracted from document OCR.")
            officer_guidance = (
                "Supporting document lacks essential field data. "
                "Officer action required to request fresh proof copy or issue information request."
            )
        else:
            recommendation = "LOW_CONFIDENCE_REVIEW"
            if not reasons:
                reasons.append("Low confidence OCR extraction or data comparison.")
            officer_guidance = (
                "Low confidence OCR extraction or data comparison observed. "
                "Thorough officer review of original document scan is required."
            )

        score_breakdown = {
            "ocr_quality": ocr_conf,
            "match_confidence": match_conf,
            "overall_score": overall_conf,
        }

        return VerificationConfidenceResult(
            ocr_confidence=ocr_conf,
            match_confidence=match_conf,
            overall_confidence=overall_conf,
            recommendation=recommendation,
            evidence_quality=evidence_quality,
            risk_flags=risk_flags,
            reasons=reasons,
            officer_guidance=officer_guidance,
            score_breakdown=score_breakdown,
        )
