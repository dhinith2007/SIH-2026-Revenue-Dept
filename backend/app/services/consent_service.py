from typing import Dict, Any, List
from datetime import datetime, timezone
from app.schemas.workflow import ConsentValidationResult
from app.core.logging import logger

# Recognized Revenue Department Recipient tokens
AUTHORIZED_RECIPIENTS = {
    "revenue_department",
    "revenue & forest department",
    "revenue and forest department",
    "maharashtra revenue department",
    "dept_revenue_forest",
}

AUTHORIZED_PURPOSES = {
    "update_revenue_address",
    "address_change",
    "residence_updation",
    "land_record_linkage",
    "address change and revenue record updation",
    "update revenue address record & 7/12 land registry linkage",
    "residence update for local tehsil record verification",
    "address record synchronization for taluka boundary verification",
}

AUTHORIZED_DATA_SCOPES = {
    "address.change",
    "address.update",
    "citizen.address",
    "revenue.record.linkage",
    "land_records.read_write",
}


class ConsentService:
    @staticmethod
    def validate_consent(app_dict: Dict[str, Any], consent_override: Dict[str, Any] = None) -> ConsentValidationResult:
        """
        Authoritatively evaluates Rules 1 through 8 for Citizen Consent.
        """
        app_id = app_dict.get("application_id", "")
        consent_ref = app_dict.get("consent_reference", "").strip()
        purpose = app_dict.get("purpose", "").strip()
        requested_op = app_dict.get("requested_operation", "").strip()

        # Seed/DB consent details or defaults
        c_record = consent_override or app_dict.get("consent_record", {})
        status = c_record.get("status", "VALID").upper()
        recipient = c_record.get("recipient", "Revenue & Forest Department").strip()
        data_scope = c_record.get("data_scope", "address.change").strip()
        expires_at = c_record.get("expires_at")
        revoked_at = c_record.get("revoked_at")

        now = datetime.now(timezone.utc)
        errors: List[str] = []
        rules: Dict[str, str] = {}

        # RULE 1: Consent reference exists
        if not consent_ref:
            errors.append("Rule 1 Failed: Consent reference is missing.")
            rules["rule_1_reference_exists"] = "FAILED"
        else:
            rules["rule_1_reference_exists"] = "PASSED"

        # RULE 2: Consent belongs to application
        target_app = c_record.get("application_id", app_id)
        if target_app != app_id:
            errors.append(f"Rule 2 Failed: Consent belongs to application '{target_app}', not '{app_id}'.")
            rules["rule_2_application_match"] = "FAILED"
        else:
            rules["rule_2_application_match"] = "PASSED"

        # RULE 3: Consent status is valid
        if status in ("EXPIRED", "REVOKED", "INVALID", "MISSING"):
            errors.append(f"Rule 3 Failed: Consent status is '{status}'.")
            rules["rule_3_status_valid"] = "FAILED"
        else:
            rules["rule_3_status_valid"] = "PASSED"

        # RULE 4: Consent not expired
        if expires_at and isinstance(expires_at, datetime):
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < now:
                errors.append(f"Rule 4 Failed: Consent expired at {expires_at.isoformat()}.")
                rules["rule_4_not_expired"] = "FAILED"
                status = "EXPIRED"
            else:
                rules["rule_4_not_expired"] = "PASSED"
        else:
            rules["rule_4_not_expired"] = "PASSED"

        # RULE 5: Consent not revoked
        if revoked_at is not None or status == "REVOKED":
            errors.append("Rule 5 Failed: Consent was revoked by citizen.")
            rules["rule_5_not_revoked"] = "FAILED"
            status = "REVOKED"
        else:
            rules["rule_5_not_revoked"] = "PASSED"

        # RULE 6: Purpose matches requested operation
        purpose_lower = purpose.lower()
        op_lower = requested_op.lower()
        if not any(k in purpose_lower or k in op_lower for k in ("address", "revenue", "land", "residence", "update")):
            errors.append("Rule 6 Failed: Consent purpose does not match requested operation.")
            rules["rule_6_purpose_match"] = "FAILED"
        else:
            rules["rule_6_purpose_match"] = "PASSED"

        # RULE 7: Data scope is authorized
        if not any(ds in data_scope.lower() for ds in ("address", "change", "citizen", "revenue")):
            errors.append(f"Rule 7 Failed: Data scope '{data_scope}' does not authorize address modifications.")
            rules["rule_7_data_scope"] = "FAILED"
        else:
            rules["rule_7_data_scope"] = "PASSED"

        # RULE 8: Revenue is an authorized recipient
        if recipient.lower() not in AUTHORIZED_RECIPIENTS and "revenue" not in recipient.lower():
            errors.append(f"Rule 8 Failed: '{recipient}' is not an authorized Revenue recipient.")
            rules["rule_8_recipient_authorized"] = "FAILED"
        else:
            rules["rule_8_recipient_authorized"] = "PASSED"

        is_valid = len(errors) == 0
        final_status = "VALID" if is_valid else (status if status != "VALID" else "INVALID")

        logger.info(
            "Consent evaluation for app '%s' (ref: %s): valid=%s, status=%s",
            app_id,
            consent_ref,
            is_valid,
            final_status,
        )

        return ConsentValidationResult(
            consent_reference=consent_ref or "CONSENT-NONE",
            application_id=app_id,
            valid=is_valid,
            status=final_status,
            purpose=purpose or "Address Record Updation",
            data_scope=data_scope,
            recipient=recipient,
            expires_at=expires_at,
            errors=errors,
            rules_evaluated=rules,
        )
