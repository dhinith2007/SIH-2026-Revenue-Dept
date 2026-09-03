from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repositories.application_repository import ApplicationRepository, _MEM_APPLICATIONS
from app.repositories.document_evidence_repository import DocumentEvidenceRepository, _MEM_EVIDENCE
from app.repositories.audit_repository import AuditRepository, _MEM_AUDIT_LOGS
from app.schemas.analytics import (
    AnalyticsSummaryKPI,
    StatusDistributionItem,
    TrendItem,
    VerificationAnalyticsResponse,
    ConfidenceAnalyticsResponse,
    RiskAnalyticsResponse,
    OfficerWorkloadItem,
    RecentActivityItem,
    FullDashboardAnalyticsResponse,
)
from app.core.logging import logger

STATUTORY_AI_DISCLAIMER = (
    "AI/OCR metrics are assistive evidence analytics. They do not constitute statutory decisions. "
    "Final decisions remain the responsibility of the authorized Revenue Officer."
)


class AnalyticsService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        evidence_repo: DocumentEvidenceRepository,
        audit_repo: AuditRepository,
    ):
        self.app_repo = app_repo
        self.evidence_repo = evidence_repo
        self.audit_repo = audit_repo

    def _filter_applications(
        self,
        apps: List[Dict[str, Any]],
        user_division: str,
        status: Optional[str] = None,
        recommendation_band: Optional[str] = None,
        risk_flag: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        filtered = []
        for app in apps:
            data_payload = app.get("data_payload", {})
            new_addr = data_payload.get("new_address", {})
            app_district = new_addr.get("district", "Pune")
            app_taluka = new_addr.get("taluka", "Haveli")

            # Division filtering (Unless super admin or state audit unit)
            if user_division and "State Audit" not in user_division and "Super Admin" not in user_division:
                clean_user_div = user_division.lower().replace("division", "").strip()
                if clean_user_div not in app_district.lower() and clean_user_div not in app_taluka.lower() and "pune" not in clean_user_div:
                    continue

            # Status filter
            if status and status.upper() != "ALL":
                if app.get("status") != status.upper():
                    continue

            # Date Range Filter
            rec_at = app.get("received_at")
            if isinstance(rec_at, str):
                try:
                    rec_at = datetime.fromisoformat(rec_at.replace("Z", "+00:00"))
                except ValueError:
                    rec_at = None

            if isinstance(rec_at, datetime):
                if rec_at.tzinfo is None:
                    rec_at = rec_at.replace(tzinfo=timezone.utc)

                if start_date and rec_at < start_date:
                    continue
                if end_date and rec_at > end_date:
                    continue

            # Document evidence filters (recommendation / risk flag)
            proof_docs = data_payload.get("proof_documents", [])
            if recommendation_band and recommendation_band.upper() != "ALL":
                has_rec = False
                for doc in proof_docs:
                    ver_res = doc.get("verification_result", {})
                    rec = ver_res.get("recommendation", "")
                    if rec.upper() == recommendation_band.upper():
                        has_rec = True
                        break
                if not has_rec:
                    continue

            if risk_flag and risk_flag.upper() != "ALL":
                has_flag = False
                for doc in proof_docs:
                    ver_res = doc.get("verification_result", {})
                    r_flags = ver_res.get("risk_flags", [])
                    if any(f.upper() == risk_flag.upper() for f in r_flags):
                        has_flag = True
                        break
                if not has_flag:
                    continue

            filtered.append(app)
        return filtered

    def get_full_dashboard_analytics(
        self,
        current_user: Dict[str, Any],
        days: int = 7,
        status: Optional[str] = None,
        recommendation_band: Optional[str] = None,
        risk_flag: Optional[str] = None,
    ) -> FullDashboardAnalyticsResponse:
        user_division = current_user.get("division", "Pune Division")
        all_apps = self.app_repo.get_all_applications()

        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        end_date = datetime.now(timezone.utc)

        filtered_apps = self._filter_applications(
            all_apps,
            user_division=user_division,
            status=status,
            recommendation_band=recommendation_band,
            risk_flag=risk_flag,
            start_date=start_date,
            end_date=end_date,
        )

        # 1. KPIs
        total_apps = len(filtered_apps)
        pending_apps = sum(1 for a in filtered_apps if a.get("status") == "PENDING")
        under_review = sum(1 for a in filtered_apps if a.get("status") == "PROCESSING")
        approved = sum(1 for a in filtered_apps if a.get("status") in ("VERIFIED", "COMPLETED"))
        rejected = sum(1 for a in filtered_apps if a.get("status") == "REJECTED")
        info_req = sum(1 for a in filtered_apps if a.get("status") == "ACTION_REQUIRED")

        doc_pending = 0
        review_req = 0
        for a in filtered_apps:
            p_docs = a.get("data_payload", {}).get("proof_documents", [])
            for d in p_docs:
                if d.get("verification_status") == "PENDING":
                    doc_pending += 1
                v_res = d.get("verification_result", {})
                rec = v_res.get("recommendation", "")
                if rec in ("LOW_CONFIDENCE_REVIEW", "MISMATCH_REVIEW", "INSUFFICIENT_EVIDENCE") or v_res.get("risk_flags"):
                    review_req += 1

        now_date = datetime.now(timezone.utc).date()
        today_apps = 0
        durations: List[float] = []
        for a in filtered_apps:
            r_at = a.get("received_at")
            if isinstance(r_at, datetime) and r_at.date() == now_date:
                today_apps += 1
            if a.get("status") in ("VERIFIED", "COMPLETED") and a.get("completed_at") and a.get("received_at"):
                r_dt = a["received_at"]
                c_dt = a["completed_at"]
                if isinstance(r_dt, datetime) and isinstance(c_dt, datetime):
                    if r_dt.tzinfo is None:
                        r_dt = r_dt.replace(tzinfo=timezone.utc)
                    if c_dt.tzinfo is None:
                        c_dt = c_dt.replace(tzinfo=timezone.utc)
                    diff_m = (c_dt - r_dt).total_seconds() / 60.0
                    if diff_m > 0:
                        durations.append(diff_m)

        avg_m = sum(durations) / len(durations) if durations else 0.0
        if avg_m > 0:
            hrs = int(avg_m // 60)
            mns = int(avg_m % 60)
            avg_str = f"{hrs}h {mns}m" if hrs > 0 else f"{mns}m"
        else:
            avg_str = "N/A"

        kpis = AnalyticsSummaryKPI(
            total_applications=total_apps,
            pending_applications=pending_apps,
            under_review=under_review,
            approved=approved,
            rejected=rejected,
            information_requested=info_req,
            document_verification_pending=doc_pending,
            review_required=review_req,
            today_applications=today_apps,
            average_processing_time_minutes=round(avg_m, 1),
            average_processing_time_str=avg_str,
        )

        # 2. Status Distribution
        status_counts = {}
        for a in filtered_apps:
            st = a.get("status", "PENDING")
            status_counts[st] = status_counts.get(st, 0) + 1

        status_dist: List[StatusDistributionItem] = []
        for st_name, count in status_counts.items():
            pct = round((count / total_apps * 100.0), 1) if total_apps > 0 else 0.0
            status_dist.append(StatusDistributionItem(status=st_name, count=count, percentage=pct))

        # 3. Trends (Time Series Daily Aggregation)
        trends_map: Dict[str, Dict[str, int]] = {}
        for i in range(days):
            d_str = (datetime.now(timezone.utc).date() - timedelta(days=days - 1 - i)).isoformat()
            trends_map[d_str] = {"incoming": 0, "approved": 0, "rejected": 0}

        for a in filtered_apps:
            r_at = a.get("received_at")
            if isinstance(r_at, datetime):
                d_str = r_at.date().isoformat()
                if d_str in trends_map:
                    trends_map[d_str]["incoming"] += 1
                    if a.get("status") in ("VERIFIED", "COMPLETED"):
                        trends_map[d_str]["approved"] += 1
                    elif a.get("status") == "REJECTED":
                        trends_map[d_str]["rejected"] += 1

        trends_list = [
            TrendItem(date=d, incoming=counts["incoming"], approved=counts["approved"], rejected=counts["rejected"])
            for d, counts in trends_map.items()
        ]

        # 4. Document Verification & OCR Metrics
        total_docs = 0
        verified_docs = 0
        pending_docs = 0
        ocr_completed = 0
        ocr_failed = 0
        ocr_conf_sum = 0.0
        match_conf_sum = 0.0
        overall_conf_sum = 0.0
        doc_count_with_conf = 0

        for a in filtered_apps:
            p_docs = a.get("data_payload", {}).get("proof_documents", [])
            total_docs += len(p_docs)
            for d in p_docs:
                v_st = d.get("verification_status")
                if v_st in ("VALIDATED", "MATCH"):
                    verified_docs += 1
                    ocr_completed += 1
                elif v_st in ("INVALID", "FAILED"):
                    ocr_failed += 1
                else:
                    pending_docs += 1

                v_res = d.get("verification_result", {})
                if v_res:
                    ocr_conf_sum += v_res.get("ocr_confidence", 0.95)
                    match_conf_sum += v_res.get("match_confidence", 1.0)
                    overall_conf_sum += v_res.get("overall_confidence", 0.96)
                    doc_count_with_conf += 1

        ocr_succ_rate = round((ocr_completed / total_docs * 100.0), 1) if total_docs > 0 else 100.0
        avg_ocr_conf = round((ocr_conf_sum / doc_count_with_conf * 100.0), 1) if doc_count_with_conf > 0 else 95.0
        avg_match_conf = round((match_conf_sum / doc_count_with_conf * 100.0), 1) if doc_count_with_conf > 0 else 100.0
        avg_overall_conf = round((overall_conf_sum / doc_count_with_conf * 100.0), 1) if doc_count_with_conf > 0 else 96.0

        verification_analytics = VerificationAnalyticsResponse(
            total_documents=total_docs,
            verified_documents=verified_docs,
            pending_documents=pending_docs,
            ocr_completed_count=ocr_completed,
            ocr_failed_count=ocr_failed,
            ocr_success_rate=ocr_succ_rate,
            average_ocr_confidence=avg_ocr_conf,
            average_match_confidence=avg_match_conf,
            average_overall_confidence=avg_overall_conf,
        )

        # 5. Confidence Distribution
        rec_counts = {
            "HIGH_CONFIDENCE_MATCH": 0,
            "MEDIUM_CONFIDENCE_REVIEW": 0,
            "LOW_CONFIDENCE_REVIEW": 0,
            "MISMATCH_REVIEW": 0,
            "INSUFFICIENT_EVIDENCE": 0,
        }
        qual_counts = {"COMPLETE": 0, "PARTIAL": 0, "INSUFFICIENT": 0, "FAILED": 0}

        for a in filtered_apps:
            p_docs = a.get("data_payload", {}).get("proof_documents", [])
            for d in p_docs:
                v_res = d.get("verification_result", {})
                rec = v_res.get("recommendation", "HIGH_CONFIDENCE_MATCH")
                qual = v_res.get("evidence_quality", "COMPLETE")
                rec_counts[rec] = rec_counts.get(rec, 0) + 1
                qual_counts[qual] = qual_counts.get(qual, 0) + 1

        confidence_analytics = ConfidenceAnalyticsResponse(
            recommendation_counts=rec_counts,
            evidence_quality_counts=qual_counts,
        )

        # 6. Risk Analytics
        risk_counts: Dict[str, int] = {}
        flagged_docs_count = 0
        for a in filtered_apps:
            p_docs = a.get("data_payload", {}).get("proof_documents", [])
            for d in p_docs:
                v_res = d.get("verification_result", {})
                flags = v_res.get("risk_flags", [])
                if flags:
                    flagged_docs_count += 1
                    for flg in flags:
                        risk_counts[flg] = risk_counts.get(flg, 0) + 1

        risk_analytics = RiskAnalyticsResponse(
            risk_flag_counts=risk_counts,
            total_flagged_documents=flagged_docs_count,
        )

        # 7. Officer Workload
        officer_map: Dict[str, Dict[str, Any]] = {
            "USR-REV-001": {"name": "Rajesh V. Patil (Desk Officer)", "assigned": 0, "pending": 0, "completed": 0},
            "USR-REV-002": {"name": "Suresh K. Deshmukh (Tahsil Officer)", "assigned": 0, "pending": 0, "completed": 0},
            "USR-REV-003": {"name": "Anil M. Joshi (Revenue Inspector)", "assigned": 0, "pending": 0, "completed": 0},
        }

        for a in filtered_apps:
            off_id = a.get("assigned_officer_id") or "USR-REV-001"
            if off_id not in officer_map:
                officer_map[off_id] = {"name": f"Officer ({off_id})", "assigned": 0, "pending": 0, "completed": 0}
            officer_map[off_id]["assigned"] += 1
            if a.get("status") in ("VERIFIED", "COMPLETED", "REJECTED"):
                officer_map[off_id]["completed"] += 1
            else:
                officer_map[off_id]["pending"] += 1

        workload_list = [
            OfficerWorkloadItem(
                officer_id=off_id,
                officer_name=info["name"],
                assigned_count=info["assigned"],
                pending_count=info["pending"],
                completed_count=info["completed"],
            )
            for off_id, info in officer_map.items()
        ]

        # 8. Recent Activity Stream
        items, _, _ = self.audit_repo.list_audit_logs(page=1, page_size=10)
        recent_activity: List[RecentActivityItem] = []
        for aud in items:
            recent_activity.append(
                RecentActivityItem(
                    id=aud.get("id", ""),
                    action=aud.get("action", "AUDIT_EVENT"),
                    officer_name=aud.get("officer_name", "Officer"),
                    application_id=aud.get("application_id", ""),
                    timestamp=aud.get("timestamp") or datetime.now(timezone.utc),
                    reason=aud.get("reason"),
                    new_status=aud.get("new_status"),
                )
            )

        return FullDashboardAnalyticsResponse(
            division=user_division,
            disclaimer=STATUTORY_AI_DISCLAIMER,
            kpis=kpis,
            status_distribution=status_dist,
            trends=trends_list,
            verification=verification_analytics,
            confidence=confidence_analytics,
            risks=risk_analytics,
            officer_workload=workload_list,
            recent_activity=recent_activity,
        )
