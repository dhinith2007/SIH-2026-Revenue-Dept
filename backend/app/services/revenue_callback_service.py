import os
import threading
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from app.core.logging import logger

DEFAULT_GOVMESH_CALLBACK_URL = "https://sih-26129-gov-mesh-citizen.vercel.app/api/govmesh/callbacks/department-status"

class RevenueCallbackService:
    @staticmethod
    def get_callback_url() -> str:
        return os.getenv("GOVMESH_CALLBACK_URL", DEFAULT_GOVMESH_CALLBACK_URL).strip()

    @classmethod
    def send_status_update_async(
        cls,
        application_id: str,
        status: str,
        correlation_id: Optional[str] = None,
        acknowledgement_id: Optional[str] = None,
        officer_id: Optional[str] = None,
        officer_name: Optional[str] = None,
        remarks: Optional[str] = None,
        request_hash: Optional[str] = None,
        document_hash: Optional[str] = None,
    ):
        """Dispatches status update to GovMesh Core asynchronously in a background thread."""
        thread = threading.Thread(
            target=cls._dispatch_callback,
            args=(
                application_id,
                status,
                correlation_id,
                acknowledgement_id,
                officer_id,
                officer_name,
                remarks,
                request_hash,
                document_hash,
            ),
            daemon=True,
        )
        thread.start()

    @classmethod
    def _dispatch_callback(
        cls,
        application_id: str,
        status: str,
        correlation_id: Optional[str] = None,
        acknowledgement_id: Optional[str] = None,
        officer_id: Optional[str] = None,
        officer_name: Optional[str] = None,
        remarks: Optional[str] = None,
        request_hash: Optional[str] = None,
        document_hash: Optional[str] = None,
    ):
        callback_url = cls.get_callback_url()
        now_utc = datetime.now(timezone.utc).isoformat()
        ack_id = acknowledgement_id or f"ACK-REV-{application_id.replace('-', '')}"
        corr_id = correlation_id or f"CORR-26-{application_id}"

        # Map local status to GovMesh canonical department status if needed
        # Local status can be PENDING, PROCESSING, VERIFIED, REJECTED, ACTION_REQUIRED
        payload = {
            "applicationId": application_id,
            "correlationId": corr_id,
            "departmentCode": "REVENUE",
            "departmentName": "Revenue & Forest Department",
            "status": status,
            "acknowledgementId": ack_id,
            "officerId": officer_id or "revenue.officer",
            "officerName": officer_name or "Revenue Officer",
            "remarks": remarks or f"Revenue Department status updated to {status}",
            "timestamp": now_utc,
            "requestHash": request_hash,
            "documentHash": document_hash,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    callback_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Department-Code": "REVENUE",
                        "X-Correlation-ID": corr_id,
                    },
                )
                logger.info(
                    "Dispatched GovMesh status callback for %s -> %s (HTTP %d)",
                    application_id,
                    status,
                    res.status_code,
                )
        except Exception as exc:
            logger.warning(
                "GovMesh status callback failed for %s (%s): %s",
                application_id,
                callback_url,
                exc,
            )

revenue_callback_service = RevenueCallbackService()
