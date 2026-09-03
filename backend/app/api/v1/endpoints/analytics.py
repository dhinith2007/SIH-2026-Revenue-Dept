from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, status, Request
from app.schemas.common import BaseResponse
from app.schemas.analytics import (
    FullDashboardAnalyticsResponse,
    AnalyticsSummaryKPI,
    StatusDistributionResponse,
    AnalyticsTrendsResponse,
    VerificationAnalyticsResponse,
    ConfidenceAnalyticsResponse,
    RiskAnalyticsResponse,
    OfficerWorkloadResponse,
    RecentActivityResponse,
)
from app.services.analytics_service import AnalyticsService
from app.api.deps import get_analytics_service, get_current_user
from app.core.simulation import check_simulated_failure
from app.core.logging import logger

router = APIRouter()


@router.get(
    "/analytics/dashboard",
    response_model=BaseResponse[FullDashboardAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Full Revenue Department Analytics & Dashboard Metrics",
    description="Returns backend-authoritative KPIs, status distribution, trends, OCR performance, AI confidence breakdown, risk flags, officer workload, and recent activity stream.",
)
async def get_full_dashboard_analytics_endpoint(
    request: Request,
    days: int = Query(7, ge=1, le=365, description="Trend calculation window in days (default 7)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by application status"),
    recommendation_band: Optional[str] = Query(None, description="Filter by AI recommendation band"),
    risk_flag: Optional[str] = Query(None, description="Filter by active risk flag"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id="ANALYTICS_DASHBOARD")
    logger.info("Full dashboard analytics requested by user '%s' (%s)", current_user["username"], current_user.get("division"))

    data = analytics_service.get_full_dashboard_analytics(
        current_user=current_user,
        days=days,
        status=status_filter,
        recommendation_band=recommendation_band,
        risk_flag=risk_flag,
    )

    return BaseResponse(
        success=True,
        data=data,
        message=f"Revenue Department analytics calculated successfully for {current_user.get('division', 'Authorized Scope')}.",
    )


@router.get(
    "/analytics/summary",
    response_model=BaseResponse[AnalyticsSummaryKPI],
    status_code=status.HTTP_200_OK,
    summary="Get Operational KPI Summary",
)
async def get_analytics_summary_kpi_endpoint(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id="ANALYTICS_KPI")
    full_data = analytics_service.get_full_dashboard_analytics(current_user=current_user)
    return BaseResponse(
        success=True,
        data=full_data.kpis,
        message="Operational KPI metrics retrieved.",
    )


@router.get(
    "/analytics/trends",
    response_model=BaseResponse[AnalyticsTrendsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Daily Time-Series Trend Aggregations",
)
async def get_analytics_trends_endpoint(
    request: Request,
    days: int = Query(7, ge=1, le=365, description="Time series window in days"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id="ANALYTICS_TRENDS")
    full_data = analytics_service.get_full_dashboard_analytics(current_user=current_user, days=days)
    return BaseResponse(
        success=True,
        data=AnalyticsTrendsResponse(items=full_data.trends, range_type=f"{days}d"),
        message=f"Time series trend analytics retrieved for last {days} days.",
    )


@router.get(
    "/analytics/verification",
    response_model=BaseResponse[VerificationAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Document Verification & OCR Performance Analytics",
)
async def get_verification_analytics_endpoint(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id="ANALYTICS_VERIFICATION")
    full_data = analytics_service.get_full_dashboard_analytics(current_user=current_user)
    return BaseResponse(
        success=True,
        data=full_data.verification,
        message="Document verification and OCR performance metrics retrieved.",
    )


@router.get(
    "/analytics/confidence",
    response_model=BaseResponse[ConfidenceAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get AI Confidence & Recommendation Distribution",
)
async def get_confidence_analytics_endpoint(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id="ANALYTICS_CONFIDENCE")
    full_data = analytics_service.get_full_dashboard_analytics(current_user=current_user)
    return BaseResponse(
        success=True,
        data=full_data.confidence,
        message="AI confidence recommendation distribution retrieved.",
    )


@router.get(
    "/analytics/risks",
    response_model=BaseResponse[RiskAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Evidence Risk Flags Analytics",
)
async def get_risk_analytics_endpoint(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id="ANALYTICS_RISKS")
    full_data = analytics_service.get_full_dashboard_analytics(current_user=current_user)
    return BaseResponse(
        success=True,
        data=full_data.risks,
        message="Risk flag analytics retrieved.",
    )
