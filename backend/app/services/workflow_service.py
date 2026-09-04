from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_repository import AuditRepository
from app.services.consent_service import ConsentService
from app.services.data_validation_service import DataValidationService
from app.services.document_verification_service import DocumentVerificationService
from app.core.errors import (
    ResourceNotFoundError,
    ApplicationFinalizedError,
    InvalidStatusTransitionError,
    ConsentInvalidError,
    DataValidationError,
    DocumentMismatchError,
)
from app.core.logging import logger
from app.services.revenue_callback_service import revenue_callback_service


class WorkflowService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        audit_repo: AuditRepository,
        notif_repo: Optional[Any] = None,
        consent_repo: Optional[Any] = None,
    ):
        self.app_repo = app_repo
        self.audit_repo = audit_repo
        self.notif_repo = notif_repo
        self.consent_repo = consent_repo

    def _emit_notif(
        self,
        notif_type: str,
        application_id: str,
        title: str,
        message: str,
        severity: str = "INFO",
        target_role: str = "ALL",
    ):
        if self.notif_repo:
            try:
                self.notif_repo.create_notification(
                    type=notif_type,
                    application_id=application_id,
                    title=title,
                    message=message,
                    severity=severity,
                    target_role=target_role,
                )
            except Exception as e:
                logger.warning("Failed to emit notification for %s: %s", application_id, e)

    def start_review(self, application_id: str, officer_id: str, officer_name: str) -> Dict[str, Any]:
        """
        Transitions application from PENDING to PROCESSING.
        """
        app = self.app_repo.get_by_application_id(application_id)
        if not app:
            raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

        current_status = app.get("status", "PENDING")
        if current_status in ("VERIFIED", "REJECTED"):
            raise ApplicationFinalizedError(
                message=f"Application '{application_id}' is already finalized in '{current_status}' state."
            )

        if current_status == "PROCESSING":
            logger.info("Application '%s' is already in PROCESSING state.", application_id)
            return app

        if current_status != "PENDING":
            raise InvalidStatusTransitionError(
                message=f"Cannot start review from status '{current_status}'. Expected 'PENDING'."
            )

        now = datetime.now(timezone.utc)
        corr_id = app.get("correlation_id", "CORR-NONE")

        timeline_event = {
            "step_name": "Desk Scrutiny Started",
            "actor": f"{officer_name} ({officer_id})",
            "action": "PROCESSING_STARTED",
            "timestamp": now.isoformat(),
            "notes": "Officer initiated formal address change scrutiny and document review.",
        }

        try:
            # 1. Update application state
            updated_app = self.app_repo.update_application_status(
                application_id=application_id,
                new_status="PROCESSING",
                assigned_officer_id=officer_id,
                processing_started_at=now,
                auto_commit=False,
            )

            # 2. Append timeline milestone
            self.app_repo.append_workflow_event(application_id, timeline_event, auto_commit=False)

            # 3. Record status history & immutable audit log
            self.audit_repo.record_status_history(
                application_id=application_id,
                previous_status=current_status,
                new_status="PROCESSING",
                action="START_REVIEW",
                changed_by=officer_name,
                reason="Desk scrutiny initiated by officer",
                correlation_id=corr_id,
                auto_commit=False,
            )
            self.audit_repo.create_audit_entry(
                officer_id=officer_id,
                officer_name=officer_name,
                application_id=application_id,
                action="START_REVIEW",
                previous_status=current_status,
                new_status="PROCESSING",
                reason="Review initiated",
                correlation_id=corr_id,
                auto_commit=False,
            )
            if self.app_repo.db:
                self.app_repo.db.commit()
        except Exception:
            if self.app_repo.db:
                self.app_repo.db.rollback()
            raise

        revenue_callback_service.send_status_update_async(
            application_id=application_id,
            status="PROCESSING",
            correlation_id=corr_id,
            officer_id=officer_id,
            officer_name=officer_name,
            remarks="Desk scrutiny initiated by Revenue officer",
            request_hash=app.get("data_payload", {}).get("canonical_hash"),
            document_hash=app.get("data_payload", {}).get("document_hash"),
        )

        return updated_app or self.app_repo.get_by_application_id(application_id)


    def approve_application(
        self, application_id: str, reason: Optional[str], officer_id: str, officer_name: str
    ) -> Dict[str, Any]:
        """
        Authoritatively approves address change application after verifying prerequisites.
        """
        app = self.app_repo.get_by_application_id(application_id)
        if not app:
            raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

        current_status = app.get("status", "PENDING")
        if current_status in ("VERIFIED", "REJECTED"):
            raise ApplicationFinalizedError(
                message=f"Application '{application_id}' has already been finalized as '{current_status}'."
            )

        # Backend Authoritative Check 1: Consent
        consent_result = ConsentService.validate_consent(app, consent_repo=self.consent_repo)
        if not consent_result.valid:
            logger.warning("Approval blocked: Consent invalid for '%s'", application_id)
            raise ConsentInvalidError(
                message=f"Approval blocked: Consent validation failed ({consent_result.status}).",
                code="CONSENT_INVALID",
                details=consent_result.errors,
            )

        # Backend Authoritative Check 2: Data Validation
        all_apps = self.app_repo.get_all_applications()
        data_result = DataValidationService.validate_application_data(app, all_apps)
        if not data_result.valid:
            logger.warning("Approval blocked: Data validation failed for '%s'", application_id)
            raise DataValidationError(
                message="Approval blocked: Data completeness validation failed.",
                code="DATA_INVALID",
                details=data_result.errors,
            )

        # Backend Authoritative Check 3: Document Verification
        doc_result = DocumentVerificationService.verify_document(app)
        if not doc_result.valid:
            logger.warning("Approval blocked: Document verification failed for '%s'", application_id)
            raise DocumentMismatchError(
                message=f"Approval blocked: Proof document verification failed ({doc_result.match_status}).",
                code="DOCUMENT_MISMATCH",
                details=doc_result.details,
            )

        now = datetime.now(timezone.utc)
        corr_id = app.get("correlation_id", "CORR-NONE")
        approval_reason = reason.strip() if reason and reason.strip() else "Address proof matches requested residence record and Taluka land registry."

        timeline_event = {
            "step_name": "Revenue Officer Approval",
            "actor": f"{officer_name} ({officer_id})",
            "action": "APPROVED",
            "timestamp": now.isoformat(),
            "notes": approval_reason,
        }

        try:
            # 1. Update application status
            updated_app = self.app_repo.update_application_status(
                application_id=application_id,
                new_status="VERIFIED",
                assigned_officer_id=officer_id,
                completed_at=now,
                required_action="Application verified & approved by Revenue Officer.",
                auto_commit=False,
            )

            # 2. Append timeline milestone
            self.app_repo.append_workflow_event(application_id, timeline_event, auto_commit=False)

            # 3. Record status history & immutable audit log
            self.audit_repo.record_status_history(
                application_id=application_id,
                previous_status=current_status,
                new_status="VERIFIED",
                action="APPROVED",
                changed_by=officer_name,
                reason=approval_reason,
                correlation_id=corr_id,
                auto_commit=False,
            )
            self.audit_repo.create_audit_entry(
                officer_id=officer_id,
                officer_name=officer_name,
                application_id=application_id,
                action="APPROVE",
                previous_status=current_status,
                new_status="VERIFIED",
                reason=approval_reason,
                correlation_id=corr_id,
                details={
                    "consent_ref": app.get("consent_reference"),
                    "new_address": app.get("data_payload", {}).get("new_address"),
                },
                auto_commit=False,
            )
            if self.app_repo.db:
                self.app_repo.db.commit()
        except Exception:
            if self.app_repo.db:
                self.app_repo.db.rollback()
            raise

        # 4. Department notification (fire and forget outside critical transaction)
        self._emit_notif(
            notif_type="WORKFLOW_COMPLETION",
            application_id=application_id,
            title="Application Verified & Approved",
            message=f"Application {application_id} for {app.get('citizen_name', 'Citizen')} has been approved.",
            severity="SUCCESS",
            target_role="ALL",
        )

        revenue_callback_service.send_status_update_async(
            application_id=application_id,
            status="VERIFIED",
            correlation_id=corr_id,
            officer_id=officer_id,
            officer_name=officer_name,
            remarks=approval_reason,
            request_hash=app.get("data_payload", {}).get("canonical_hash"),
            document_hash=app.get("data_payload", {}).get("document_hash"),
        )

        logger.info("Application '%s' successfully APPROVED by %s", application_id, officer_name)
        return updated_app or self.app_repo.get_by_application_id(application_id)

    def reject_application(
        self, application_id: str, reason: str, officer_id: str, officer_name: str
    ) -> Dict[str, Any]:
        """
        Authoritatively rejects application with statutory reason.
        """
        app = self.app_repo.get_by_application_id(application_id)
        if not app:
            raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

        current_status = app.get("status", "PENDING")
        if current_status in ("VERIFIED", "REJECTED"):
            raise ApplicationFinalizedError(
                message=f"Application '{application_id}' has already been finalized as '{current_status}'."
            )

        if not reason or len(reason.strip()) < 5:
            raise DataValidationError(
                message="A meaningful rejection reason (minimum 5 characters) is mandatory.",
                code="REJECTION_REASON_REQUIRED",
            )

        now = datetime.now(timezone.utc)
        corr_id = app.get("correlation_id", "CORR-NONE")
        rejection_reason = reason.strip()

        timeline_event = {
            "step_name": "Revenue Officer Rejection",
            "actor": f"{officer_name} ({officer_id})",
            "action": "REJECTED",
            "timestamp": now.isoformat(),
            "notes": rejection_reason,
        }

        try:
            # 1. Update application status
            updated_app = self.app_repo.update_application_status(
                application_id=application_id,
                new_status="REJECTED",
                assigned_officer_id=officer_id,
                completed_at=now,
                required_action=f"Application rejected. Reason: {rejection_reason}",
                auto_commit=False,
            )

            # 2. Append timeline milestone
            self.app_repo.append_workflow_event(application_id, timeline_event, auto_commit=False)

            # 3. Record status history & immutable audit log
            self.audit_repo.record_status_history(
                application_id=application_id,
                previous_status=current_status,
                new_status="REJECTED",
                action="REJECTED",
                changed_by=officer_name,
                reason=rejection_reason,
                correlation_id=corr_id,
                auto_commit=False,
            )
            self.audit_repo.create_audit_entry(
                officer_id=officer_id,
                officer_name=officer_name,
                application_id=application_id,
                action="REJECT",
                previous_status=current_status,
                new_status="REJECTED",
                reason=rejection_reason,
                correlation_id=corr_id,
                auto_commit=False,
            )
            if self.app_repo.db:
                self.app_repo.db.commit()
        except Exception:
            if self.app_repo.db:
                self.app_repo.db.rollback()
            raise

        # 4. Department notification (fire and forget)
        self._emit_notif(
            notif_type="WORKFLOW_COMPLETION",
            application_id=application_id,
            title="Application Rejected",
            message=f"Application {application_id} rejected. Reason: {rejection_reason}",
            severity="WARNING",
            target_role="ALL",
        )

        revenue_callback_service.send_status_update_async(
            application_id=application_id,
            status="REJECTED",
            correlation_id=corr_id,
            officer_id=officer_id,
            officer_name=officer_name,
            remarks=rejection_reason,
            request_hash=app.get("data_payload", {}).get("canonical_hash"),
            document_hash=app.get("data_payload", {}).get("document_hash"),
        )

        logger.info("Application '%s' REJECTED by %s. Reason: %s", application_id, officer_name, rejection_reason)
        return updated_app or self.app_repo.get_by_application_id(application_id)


    def request_additional_information(
        self, application_id: str, request_type: str, message: str, officer_id: str, officer_name: str
    ) -> Dict[str, Any]:
        """
        Transitions application to ACTION_REQUIRED when citizen clarification or missing document is needed.
        """
        app = self.app_repo.get_by_application_id(application_id)
        if not app:
            raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

        current_status = app.get("status", "PENDING")
        if current_status in ("VERIFIED", "REJECTED"):
            raise ApplicationFinalizedError(
                message=f"Application '{application_id}' is finalized and cannot request additional info."
            )

        if not message or len(message.strip()) < 5:
            raise DataValidationError(
                message="Information request message (minimum 5 characters) is mandatory.",
                code="MESSAGE_REQUIRED",
            )

        now = datetime.now(timezone.utc)
        corr_id = app.get("correlation_id", "CORR-NONE")
        req_msg = message.strip()
        req_action_desc = f"Citizen Information Required [{request_type}]: {req_msg}"

        timeline_event = {
            "step_name": f"Department Query Raised ({request_type})",
            "actor": f"{officer_name} ({officer_id})",
            "action": "INFORMATION_REQUESTED",
            "timestamp": now.isoformat(),
            "notes": req_msg,
        }

        try:
            # 1. Update application status
            updated_app = self.app_repo.update_application_status(
                application_id=application_id,
                new_status="ACTION_REQUIRED",
                assigned_officer_id=officer_id,
                required_action=req_action_desc,
                auto_commit=False,
            )

            # 2. Append timeline milestone
            self.app_repo.append_workflow_event(application_id, timeline_event, auto_commit=False)

            # 3. Record status history & immutable audit log
            self.audit_repo.record_status_history(
                application_id=application_id,
                previous_status=current_status,
                new_status="ACTION_REQUIRED",
                action="INFORMATION_REQUESTED",
                changed_by=officer_name,
                reason=f"[{request_type}] {req_msg}",
                correlation_id=corr_id,
                auto_commit=False,
            )
            self.audit_repo.create_audit_entry(
                officer_id=officer_id,
                officer_name=officer_name,
                application_id=application_id,
                action="REQUEST_INFORMATION",
                previous_status=current_status,
                new_status="ACTION_REQUIRED",
                reason=f"[{request_type}] {req_msg}",
                correlation_id=corr_id,
                details={"request_type": request_type, "message": req_msg},
                auto_commit=False,
            )
            if self.app_repo.db:
                self.app_repo.db.commit()
        except Exception:
            if self.app_repo.db:
                self.app_repo.db.rollback()
            raise

        # 4. Department notification (fire and forget)
        self._emit_notif(
            notif_type="ACTION_REQUIRED",
            application_id=application_id,
            title=f"Query Raised ({request_type})",
            message=f"Officer {officer_name} requested information for application {application_id}: {req_msg}",
            severity="WARNING",
            target_role="REVENUE_OFFICER",
        )

        revenue_callback_service.send_status_update_async(
            application_id=application_id,
            status="ACTION_REQUIRED",
            correlation_id=corr_id,
            officer_id=officer_id,
            officer_name=officer_name,
            remarks=req_action_desc,
            request_hash=app.get("data_payload", {}).get("canonical_hash"),
            document_hash=app.get("data_payload", {}).get("document_hash"),
        )

        logger.info("Information requested for '%s' by %s: %s", application_id, officer_name, req_action_desc)
        return updated_app or self.app_repo.get_by_application_id(application_id)

    def reprocess_application(self, application_id: str, officer_id: str, officer_name: str) -> Dict[str, Any]:
        """
        Simulated re-submission: resets ACTION_REQUIRED back to PROCESSING for re-verification.
        """
        app = self.app_repo.get_by_application_id(application_id)
        if not app:
            raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

        current_status = app.get("status")
        if current_status in ("VERIFIED", "REJECTED"):
            raise ApplicationFinalizedError(
                message=f"Application '{application_id}' is already finalized in '{current_status}' state."
            )

        if current_status != "ACTION_REQUIRED":
            raise InvalidStatusTransitionError(
                message=f"Cannot reprocess application from status '{current_status}'. Expected 'ACTION_REQUIRED'."
            )

        now = datetime.now(timezone.utc)
        corr_id = app.get("correlation_id", "CORR-NONE")

        timeline_event = {
            "step_name": "Citizen Response Ingested (Reprocessing)",
            "actor": "Citizen (via GovMesh Channel)",
            "action": "REPROCESSED",
            "timestamp": now.isoformat(),
            "notes": "Supplementary address proof document submitted for desk re-scrutiny.",
        }

        try:
            # 1. Update application status
            updated_app = self.app_repo.update_application_status(
                application_id=application_id,
                new_status="PROCESSING",
                assigned_officer_id=officer_id,
                required_action="Re-verification in progress following citizen information submission.",
                auto_commit=False,
            )

            # 2. Append timeline milestone
            self.app_repo.append_workflow_event(application_id, timeline_event, auto_commit=False)

            # 3. Record status history & immutable audit log
            self.audit_repo.record_status_history(
                application_id=application_id,
                previous_status="ACTION_REQUIRED",
                new_status="PROCESSING",
                action="REPROCESSED",
                changed_by=officer_name,
                reason="Citizen uploaded supplementary document",
                correlation_id=corr_id,
                auto_commit=False,
            )
            self.audit_repo.create_audit_entry(
                officer_id=officer_id,
                officer_name=officer_name,
                application_id=application_id,
                action="REPROCESS",
                previous_status="ACTION_REQUIRED",
                new_status="PROCESSING",
                reason="Reprocessing initiated",
                correlation_id=corr_id,
                auto_commit=False,
            )
            if self.app_repo.db:
                self.app_repo.db.commit()
        except Exception:
            if self.app_repo.db:
                self.app_repo.db.rollback()
            raise

        # 4. Department notification (fire and forget)
        self._emit_notif(
            notif_type="CITIZEN_RESPONSE",
            application_id=application_id,
            title="Citizen Response Received",
            message=f"Citizen response ingested for application {application_id}. Ready for re-verification.",
            severity="INFO",
            target_role="REVENUE_OFFICER",
        )

        revenue_callback_service.send_status_update_async(
            application_id=application_id,
            status="PROCESSING",
            correlation_id=corr_id,
            officer_id=officer_id,
            officer_name=officer_name,
            remarks="Reprocessing following supplementary document submission",
            request_hash=app.get("data_payload", {}).get("canonical_hash"),
            document_hash=app.get("data_payload", {}).get("document_hash"),
        )

        logger.info("Application '%s' REPROCESSED back to PROCESSING by %s", application_id, officer_name)
        return updated_app or self.app_repo.get_by_application_id(application_id)

    def retry_application(self, application_id: str, officer_id: str, officer_name: str) -> Dict[str, Any]:
        """
        Controlled retry mechanism for transient failure recovery (Phase 05).
        Preserves application ID & correlation ID without duplicating records.
        """
        app = self.app_repo.get_by_application_id(application_id)
        if not app:
            raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

        current_status = app.get("status", "PENDING")
        if current_status in ("VERIFIED", "REJECTED"):
            raise ApplicationFinalizedError(
                message=f"Cannot retry application '{application_id}' as it is already finalized in '{current_status}' state."
            )

        now = datetime.now(timezone.utc)
        corr_id = app.get("correlation_id", "CORR-NONE")
        target_status = "PROCESSING" if current_status != "PENDING" else "PENDING"

        timeline_event = {
            "step_name": "Controlled Operational Retry Ingested",
            "actor": f"{officer_name} ({officer_id})",
            "action": "RETRY_RECEIVED",
            "timestamp": now.isoformat(),
            "notes": "Operational retry executed. Verification checks re-evaluated without duplicating record.",
        }

        try:
            # 1. Transition status back to PROCESSING or PENDING
            updated_app = self.app_repo.update_application_status(
                application_id=application_id,
                new_status=target_status,
                assigned_officer_id=officer_id,
                required_action="Desk scrutiny resumed following controlled failure retry.",
                auto_commit=False,
            )

            # 2. Append timeline milestone
            self.app_repo.append_workflow_event(application_id, timeline_event, auto_commit=False)

            # 3. Record status history & immutable audit log
            self.audit_repo.record_status_history(
                application_id=application_id,
                previous_status=current_status,
                new_status=target_status,
                action="RETRY_RECEIVED",
                changed_by=officer_name,
                reason="Controlled operational retry initiated",
                correlation_id=corr_id,
                auto_commit=False,
            )
            self.audit_repo.create_audit_entry(
                officer_id=officer_id,
                officer_name=officer_name,
                application_id=application_id,
                action="RETRY",
                previous_status=current_status,
                new_status=target_status,
                reason="Operational retry initiated",
                correlation_id=corr_id,
                auto_commit=False,
            )
            if self.app_repo.db:
                self.app_repo.db.commit()
        except Exception:
            if self.app_repo.db:
                self.app_repo.db.rollback()
            raise

        # 4. Department notification (fire and forget)
        self._emit_notif(
            notif_type="RETRY_RECEIVED",
            application_id=application_id,
            title="Operational Retry Received",
            message=f"Application {application_id} retry ingested by {officer_name}. Scrutiny resumed.",
            severity="INFO",
            target_role="REVENUE_OFFICER",
        )

        revenue_callback_service.send_status_update_async(
            application_id=application_id,
            status=target_status,
            correlation_id=corr_id,
            officer_id=officer_id,
            officer_name=officer_name,
            remarks="Operational retry initiated",
            request_hash=app.get("data_payload", {}).get("canonical_hash"),
            document_hash=app.get("data_payload", {}).get("document_hash"),
        )

        logger.info("Application '%s' RETRIED to %s by %s", application_id, target_status, officer_name)
        return updated_app or self.app_repo.get_by_application_id(application_id)


