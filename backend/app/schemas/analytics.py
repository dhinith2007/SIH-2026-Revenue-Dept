from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnalyticsSummaryKPI(BaseModel):
    total_applications: int = Field(..., description="Total applications in authorized division scope")
    pending_applications: int = Field(..., description="Applications awaiting scrutiny")
    under_review: int = Field(..., description="Applications under active officer processing")
    approved: int = Field(..., description="Applications statutorily approved / verified")
    rejected: int = Field(..., description="Applications rejected")
    information_requested: int = Field(..., description="Applications awaiting citizen clarification")
    document_verification_pending: int = Field(..., description="Proof documents awaiting verification")
    review_required: int = Field(..., description="Applications with high risk or mismatch indicators")
    today_applications: int = Field(..., description="Applications ingested today")
    average_processing_time_minutes: float = Field(0.0, description="Average processing duration in minutes")
    average_processing_time_str: str = Field("N/A", description="Formatted average processing duration")


class StatusDistributionItem(BaseModel):
    status: str
    count: int
    percentage: float


class StatusDistributionResponse(BaseModel):
    items: List[StatusDistributionItem]
    total: int


class TrendItem(BaseModel):
    date: str  # YYYY-MM-DD
    incoming: int
    approved: int
    rejected: int


class AnalyticsTrendsResponse(BaseModel):
    items: List[TrendItem]
    range_type: str = "7d"


class VerificationAnalyticsResponse(BaseModel):
    total_documents: int
    verified_documents: int
    pending_documents: int
    ocr_completed_count: int
    ocr_failed_count: int
    ocr_success_rate: float
    average_ocr_confidence: float
    average_match_confidence: float
    average_overall_confidence: float


class ConfidenceAnalyticsResponse(BaseModel):
    recommendation_counts: Dict[str, int] = Field(
        default_factory=lambda: {
            "HIGH_CONFIDENCE_MATCH": 0,
            "MEDIUM_CONFIDENCE_REVIEW": 0,
            "LOW_CONFIDENCE_REVIEW": 0,
            "MISMATCH_REVIEW": 0,
            "INSUFFICIENT_EVIDENCE": 0,
        }
    )
    evidence_quality_counts: Dict[str, int] = Field(
        default_factory=lambda: {
            "COMPLETE": 0,
            "PARTIAL": 0,
            "INSUFFICIENT": 0,
            "FAILED": 0,
        }
    )


class RiskAnalyticsResponse(BaseModel):
    risk_flag_counts: Dict[str, int] = Field(default_factory=dict)
    total_flagged_documents: int = 0


class OfficerWorkloadItem(BaseModel):
    officer_id: str
    officer_name: str
    assigned_count: int
    pending_count: int
    completed_count: int


class OfficerWorkloadResponse(BaseModel):
    items: List[OfficerWorkloadItem]


class RecentActivityItem(BaseModel):
    id: str
    action: str
    officer_name: str
    application_id: str
    timestamp: datetime
    reason: Optional[str] = None
    new_status: Optional[str] = None


class RecentActivityResponse(BaseModel):
    items: List[RecentActivityItem]


class FullDashboardAnalyticsResponse(BaseModel):
    division: str
    disclaimer: str = (
        "AI/OCR metrics are assistive evidence analytics. They do not constitute statutory decisions. "
        "Final decisions remain the responsibility of the authorized Revenue Officer."
    )
    kpis: AnalyticsSummaryKPI
    status_distribution: List[StatusDistributionItem]
    trends: List[TrendItem]
    verification: VerificationAnalyticsResponse
    confidence: ConfidenceAnalyticsResponse
    risks: RiskAnalyticsResponse
    officer_workload: List[OfficerWorkloadItem]
    recent_activity: List[RecentActivityItem]
