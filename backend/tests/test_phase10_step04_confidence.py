import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.services.ocr.base import OCRRawResult, OCRExtractedField
from app.services.ocr.confidence_engine import (
    RuleBasedVerificationConfidenceEngine,
    VerificationConfidenceResult,
)
from app.services.document_verification_service import DocumentVerificationService
from app.schemas.workflow import DocumentVerificationResult


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def desk_officer_token():
    return create_access_token(
        data={
            "sub": "USR-REV-001",
            "username": "revenue.officer",
            "role": "REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Pune Division",
        }
    )


@pytest.fixture
def other_officer_token():
    return create_access_token(
        data={
            "sub": "USR-REV-006",
            "username": "other.officer",
            "role": "REVENUE_OFFICER",
            "department": "Revenue & Forest Department",
            "division": "Pune Division (Baramati Tahsil)",
        }
    )


@pytest.fixture
def auditor_token():
    return create_access_token(
        data={
            "sub": "USR-REV-004",
            "username": "auditor.internal",
            "role": "READ_ONLY_AUDITOR",
            "department": "Revenue & Forest Department",
            "division": "State Audit Unit",
        }
    )


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Scenario A: High-Confidence Scenario
# ============================================================================
def test_high_confidence_recommendation():
    ocr_raw = OCRRawResult(
        provider="SIMULATED",
        status="SUCCESS",
        overall_confidence=0.95,
    )
    name_eval = {"result": "MATCH", "score": 1.0}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MATCH", "score": 1.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=1.0)

    assert isinstance(res, VerificationConfidenceResult)
    assert res.recommendation == "HIGH_CONFIDENCE_MATCH"
    assert res.evidence_quality == "COMPLETE"
    assert res.overall_confidence >= 0.88
    assert len(res.risk_flags) == 0
    assert "standard officer statutory review" in res.officer_guidance.lower()


# ============================================================================
# Scenario B: Medium-Confidence Scenario (Low OCR / Partial Match)
# ============================================================================
def test_medium_confidence_due_to_low_ocr_quality():
    ocr_raw = OCRRawResult(
        provider="TESSERACT",
        status="SUCCESS",
        overall_confidence=0.65,  # Low OCR quality
    )
    name_eval = {"result": "MATCH", "score": 1.0}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MATCH", "score": 1.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=1.0)

    assert res.recommendation == "MEDIUM_CONFIDENCE_REVIEW"
    assert "OCR_LOW_CONFIDENCE" in res.risk_flags
    assert res.ocr_confidence == 0.65


# ============================================================================
# Scenario C: Low Confidence / Insufficient Evidence Scenario
# ============================================================================
def test_insufficient_evidence_when_fields_missing():
    ocr_raw = OCRRawResult(
        provider="TESSERACT",
        status="SUCCESS",
        overall_confidence=0.80,
    )
    name_eval = {"result": "NOT_EXTRACTED", "score": 0.0}
    comp_eval = {
        "house_no": {"result": "NOT_EXTRACTED", "score": 0.0},
        "street": {"result": "NOT_EXTRACTED", "score": 0.0},
        "village": {"result": "NOT_EXTRACTED", "score": 0.0},
        "taluka": {"result": "NOT_EXTRACTED", "score": 0.0},
        "district": {"result": "NOT_EXTRACTED", "score": 0.0},
        "pincode": {"result": "NOT_EXTRACTED", "score": 0.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.0)

    assert res.recommendation == "INSUFFICIENT_EVIDENCE"
    assert res.evidence_quality == "INSUFFICIENT"
    assert "MISSING_CRITICAL_FIELD" in res.risk_flags


# ============================================================================
# Scenario D: Pincode Mismatch Override
# ============================================================================
def test_pincode_mismatch_triggers_mismatch_review():
    ocr_raw = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=0.95)
    name_eval = {"result": "MATCH", "score": 1.0}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MISMATCH", "score": 0.0, "explanation": "App 600095 vs Doc 600096"},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.85)

    assert res.recommendation == "MISMATCH_REVIEW"
    assert res.recommendation != "HIGH_CONFIDENCE_MATCH"
    assert "PINCODE_MISMATCH" in res.risk_flags
    assert res.overall_confidence <= 0.40


# ============================================================================
# Scenario E: District Mismatch Override
# ============================================================================
def test_district_mismatch_triggers_mismatch_review():
    ocr_raw = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=0.95)
    name_eval = {"result": "MATCH", "score": 1.0}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MISMATCH", "score": 0.0, "explanation": "App Pune vs Doc Nagpur"},
        "pincode": {"result": "MATCH", "score": 1.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.85)

    assert res.recommendation == "MISMATCH_REVIEW"
    assert "DISTRICT_MISMATCH" in res.risk_flags


# ============================================================================
# Scenario F: Name Mismatch Override
# ============================================================================
def test_name_mismatch_triggers_mismatch_review():
    ocr_raw = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=0.95)
    name_eval = {"result": "MISMATCH", "score": 0.20, "document_value": "Suresh Kulkarni", "application_value": "Rajesh Patil"}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MATCH", "score": 1.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.85)

    assert res.recommendation == "MISMATCH_REVIEW"
    assert "NAME_MISMATCH" in res.risk_flags


# ============================================================================
# Scenario G: Script Difference Handling
# ============================================================================
def test_script_difference_triggers_medium_review():
    ocr_raw = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=0.95)
    name_eval = {"result": "PARTIAL_MATCH", "method": "script_difference", "score": 0.50}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MATCH", "score": 1.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.90)

    assert res.recommendation == "MEDIUM_CONFIDENCE_REVIEW"
    assert "SCRIPT_DIFFERENCE" in res.risk_flags


# ============================================================================
# Scenario H: OCR Extraction Failure Handling
# ============================================================================
def test_ocr_failure_yields_failed_quality_and_insufficient_evidence():
    ocr_raw = OCRRawResult(provider="TESSERACT", status="FAILED", overall_confidence=0.0, error_message="Binary unreadable")
    name_eval = {"result": "NOT_EXTRACTED", "score": 0.0}
    comp_eval = {}

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.0)

    assert res.recommendation == "INSUFFICIENT_EVIDENCE"
    assert res.evidence_quality == "FAILED"
    assert "OCR_FAILED" in res.risk_flags
    assert res.overall_confidence == 0.0


# ============================================================================
# Scenario I: Confidence Metric Separation
# ============================================================================
def test_ocr_vs_match_vs_overall_confidence_metrics_distinct():
    ocr_raw = OCRRawResult(provider="TESSERACT", status="SUCCESS", overall_confidence=0.75)
    name_eval = {"result": "MATCH", "score": 1.0}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MATCH", "score": 1.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.90)

    assert res.ocr_confidence == 0.75
    assert res.match_confidence == 0.90
    assert res.overall_confidence != res.ocr_confidence
    assert res.overall_confidence != res.match_confidence


# ============================================================================
# Scenario J: Determinism
# ============================================================================
def test_confidence_engine_determinism():
    ocr_raw = OCRRawResult(provider="SIMULATED", status="SUCCESS", overall_confidence=0.92)
    name_eval = {"result": "MATCH", "score": 1.0}
    comp_eval = {
        "house_no": {"result": "MATCH", "score": 1.0},
        "street": {"result": "MATCH", "score": 1.0},
        "village": {"result": "MATCH", "score": 1.0},
        "taluka": {"result": "MATCH", "score": 1.0},
        "district": {"result": "MATCH", "score": 1.0},
        "pincode": {"result": "MATCH", "score": 1.0},
    }

    engine = RuleBasedVerificationConfidenceEngine()
    res1 = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.98)
    res2 = engine.evaluate_confidence(ocr_raw, name_eval, comp_eval, assistive_score=0.98)

    assert res1.recommendation == res2.recommendation
    assert res1.overall_confidence == res2.overall_confidence
    assert res1.risk_flags == res2.risk_flags
    assert res1.reasons == res2.reasons


# ============================================================================
# Scenario K: Human-in-the-Loop & Statutory Approval Safety
# ============================================================================
def test_confidence_engine_never_causes_statutory_approval(client, desk_officer_token):
    # GM-2026-000129 has document mismatch
    # Attempting to approve without overriding must be blocked with HTTP 422
    res = client.post(
        "/api/v1/revenue/application/GM-2026-000129/approve",
        json={"reason": "Officer attempting approval without addressing document mismatch"},
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DOCUMENT_MISMATCH"


# ============================================================================
# Scenario L: Security Invariants
# ============================================================================
def test_cross_division_officer_cannot_trigger_ocr_verification(client, other_officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(other_officer_token),
    )
    assert res.status_code == 403


def test_auditor_read_only_restriction(client, auditor_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-9081/verify",
        headers=auth_header(auditor_token),
    )
    assert res.status_code == 403


def test_finalized_application_document_override_blocked(client, desk_officer_token):
    res = client.post(
        "/api/v1/revenue/document/DOC-REV-3310/override",
        json={"decision": "MISMATCH", "reason": "Officer attempting to alter finalized state."},
        headers=auth_header(desk_officer_token),
    )
    assert res.status_code == 409
