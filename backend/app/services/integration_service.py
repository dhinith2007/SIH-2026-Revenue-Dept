from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone, timedelta
from app.schemas.integration import ApplicationIngestRequest, ApplicationIngestResponse
from app.repositories.application_repository import ApplicationRepository
from app.repositories.consent_repository import ConsentRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.notification_repository import NotificationRepository
from app.core.config import settings
from app.core.errors import RevenueAppException
from app.core.logging import logger


class IntegrationService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        consent_repo: ConsentRepository,
        audit_repo: AuditRepository,
        notif_repo: Optional[NotificationRepository] = None,
    ):
        self.app_repo = app_repo
        self.consent_repo = consent_repo
        self.audit_repo = audit_repo
        self.notif_repo = notif_repo

    def ingest_application(
        self,
        payload: ApplicationIngestRequest,
        client_ip: str = "unknown",
    ) -> Tuple[ApplicationIngestResponse, int]:
        """
        Receives, validates, checks idempotency, and atomically persists a new external
        citizen application from the GovMesh Integration Layer or external departments.
        
        Returns:
            (ApplicationIngestResponse, 201) for newly received applications.
            (ApplicationIngestResponse, 200) for idempotent duplicate deliveries.
        """
        app_id = payload.application_id.strip()
        corr_id = payload.correlation_id.strip()

        # 1. Validate Integration Contract Version
        if payload.request_version not in settings.SUPPORTED_INTEGRATION_VERSIONS:
            logger.warning("Rejected integration submission: unsupported version '%s' for '%s'", payload.request_version, app_id)
            raise RevenueAppException(
                code="UNSUPPORTED_CONTRACT_VERSION",
                message=f"Integration contract version '{payload.request_version}' is unsupported. Supported versions: {', '.join(settings.SUPPORTED_INTEGRATION_VERSIONS)}",
                status_code=400,
                correlation_id=corr_id,
            )

        # 2. Idempotency & Duplicate Check
        existing = self.app_repo.get_by_application_id(app_id)
        if existing:
            # Check if this is an idempotent duplicate delivery
            existing_corr = existing.get("correlation_id", "")
            existing_citizen = existing.get("citizen_name", "")
            
            # If same correlation ID or citizen identity, return safe idempotent 200 OK
            if existing_corr == corr_id or existing_citizen.strip().lower() == payload.citizen.name.strip().lower():
                logger.info("Idempotent duplicate application '%s' acknowledged safely (Status: %s)", app_id, existing.get("status"))
                recv_at = existing.get("received_at")
                if isinstance(recv_at, str):
                    try:
                        recv_at = datetime.fromisoformat(recv_at)
                    except Exception:
                        recv_at = datetime.now(timezone.utc)
                elif not isinstance(recv_at, datetime):
                    recv_at = datetime.now(timezone.utc)

                return (
                    ApplicationIngestResponse(
                        success=True,
                        status="ALREADY_RECEIVED",
                        application_id=app_id,
                        correlation_id=corr_id,
                        message="Application was already received",
                        received_at=recv_at,
                    ),
                    200,
                )
            else:
                # Conflicting application identity using the same application_id
                logger.warning("Conflict: Application ID '%s' exists with mismatched citizen/correlation ID", app_id)
                raise RevenueAppException(
                    code="APPLICATION_ID_CONFLICT",
                    message=f"Application ID '{app_id}' already exists with conflicting citizen or correlation identity.",
                    status_code=409,
                    correlation_id=corr_id,
                )

        # 3. Transform DTO to Revenue Domain Entity
        now = datetime.now(timezone.utc)
        sub_time = payload.submitted_at or now

        # Determine effective consent reference
        c_ref = (
            payload.consent.get_effective_reference(app_id)
            if payload.consent
            else f"CONSENT-{app_id.replace('GM-', '')}"
        )
        purpose_str = (
            payload.consent.purpose
            if payload.consent and payload.consent.purpose
            else "Update Revenue address record & 7/12 land registry linkage"
        )

        app_dict = {
            "id": f"APP-{app_id}",
            "application_id": app_id,
            "correlation_id": corr_id,
            "citizen_reference_id": payload.citizen.identifier,
            "service_type": payload.service_type,
            "requested_operation": "UPDATE_REVENUE_ADDRESS",
            "purpose": purpose_str,
            "consent_reference": c_ref,
            "priority": (payload.priority or "NORMAL").upper(),
            "status": "PENDING",
            "required_action": "Verify new residential address against Taluka land registry & electricity proof",
            "citizen_name": payload.citizen.name,
            "received_at": sub_time,
            "updated_at": now,
            "processing_started_at": None,
            "completed_at": None,
            "assigned_officer_id": None,
            "data_payload": {
                "citizen_name": payload.citizen.name,
                "citizen_contact": payload.citizen.contact.model_dump() if payload.citizen.contact else None,
                "existing_address": payload.application_data.existing_address.model_dump() if payload.application_data.existing_address else None,
                "new_address": payload.application_data.new_address.model_dump(),
                "proof_documents": [d.model_dump() for d in payload.application_data.proof_documents] if payload.application_data.proof_documents else [],
                "remarks": payload.application_data.remarks or "Application submitted via GovMesh citizen portal",
                "integration_metadata": {
                    "source_department": payload.source_department,
                    "request_version": payload.request_version,
                    "submitted_at": sub_time.isoformat(),
                    "canonical_hash": payload.integrity.canonical_hash if payload.integrity else None,
                    "document_hash": payload.integrity.document_hash if payload.integrity else None,
                    "ingested_from_ip": client_ip,
                },
            },
            "workflow_history": [
                {
                    "step_name": "GovMesh Cross-Department Ingestion",
                    "actor": f"GovMesh Integration Gateway ({payload.source_department})",
                    "action": "APPLICATION_RECEIVED",
                    "timestamp": now.isoformat(),
                    "notes": f"Application ingested via Cross-Department Contract v{payload.request_version}.",
                }
            ],
        }

        # 4. Atomic Multi-Entity Persistence
        try:
            # A. Create application record
            self.app_repo.create_new_application(app_dict, auto_commit=False)

            # B. Create legal consent record
            if payload.consent:
                exp_date = payload.consent.expires_at or (now + timedelta(days=365))
                consent_data = {
                    "id": f"CONS-{c_ref}",
                    "consent_reference": c_ref,
                    "application_id": app_id,
                    "status": "VALID" if payload.consent.granted else "INVALID",
                    "purpose": purpose_str,
                    "data_scope": payload.consent.data_scope or "address.change",
                    "recipient": payload.consent.recipient or "Revenue & Forest Department",
                    "issued_at": payload.consent.issued_at or now,
                    "expires_at": exp_date,
                    "revoked_at": None,
                    "validated_at": None,
                    "validation_result": None,
                }
                self.consent_repo.create_consent(consent_data, auto_commit=False)

            # C. Record application status history
            self.audit_repo.record_status_history(
                application_id=app_id,
                previous_status=None,
                new_status="PENDING",
                action="APPLICATION_RECEIVED",
                changed_by=f"GovMesh Gateway ({payload.source_department})",
                reason="New cross-department application ingestion",
                correlation_id=corr_id,
                auto_commit=False,
            )

            # D. Record immutable audit log
            self.audit_repo.create_audit_entry(
                officer_id="EXT-GOVMESH",
                officer_name=f"GovMesh Gateway ({payload.source_department})",
                application_id=app_id,
                action="APPLICATION_INGESTED",
                previous_status=None,
                new_status="PENDING",
                reason="Cross-department ingestion via GovMesh integration contract",
                correlation_id=corr_id,
                details={
                    "source_department": payload.source_department,
                    "request_version": payload.request_version,
                    "citizen_name": payload.citizen.name,
                    "taluka": payload.application_data.new_address.taluka,
                    "district": payload.application_data.new_address.district,
                    "pincode": payload.application_data.new_address.pincode,
                },
                auto_commit=False,
            )

            # E. Commit transaction atomically
            if self.app_repo.db:
                self.app_repo.db.commit()

        except Exception as exc:
            if self.app_repo.db:
                self.app_repo.db.rollback()
            logger.error("Transaction failed during application ingestion for '%s': %s", app_id, exc, exc_info=True)
            raise RevenueAppException(
                code="PERSISTENCE_ERROR",
                message="Failed to commit application record to departmental storage.",
                status_code=500,
                correlation_id=corr_id,
                details=str(exc),
            )

        # 5. Emit departmental notification (outside critical transaction)
        if self.notif_repo:
            try:
                self.notif_repo.create_notification(
                    type="APPLICATION_RECEIVED",
                    application_id=app_id,
                    title="New Cross-Department Application",
                    message=f"Application {app_id} received from {payload.source_department} for {payload.citizen.name} ({payload.application_data.new_address.taluka} Taluka).",
                    severity="INFO",
                    target_role="ALL",
                )
            except Exception as ne:
                logger.warning("Notification emission failed for %s: %s", app_id, ne)

        logger.info("Application '%s' successfully ingested into Revenue Department records.", app_id)
        return (
            ApplicationIngestResponse(
                success=True,
                status="RECEIVED",
                application_id=app_id,
                correlation_id=corr_id,
                message="Application successfully received by Revenue Department",
                received_at=sub_time,
            ),
            201,
        )
