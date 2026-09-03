import re
from typing import Dict, Any, List, Optional
from app.schemas.workflow import DataValidationResult
from app.services.consent_service import ConsentService
from app.core.logging import logger


class DataValidationService:
    @staticmethod
    def validate_application_data(app_dict: Dict[str, Any], all_apps: Optional[List[Dict[str, Any]]] = None) -> DataValidationResult:
        """
        Authoritatively validates Revenue Address Change payload data.
        """
        app_id = app_dict.get("application_id", "")
        data_payload = app_dict.get("data_payload", {})
        existing_addr = data_payload.get("existing_address", {})
        new_addr = data_payload.get("new_address", {})
        proof_docs = data_payload.get("proof_documents", [])
        citizen_name = app_dict.get("citizen_name", "").strip() or data_payload.get("citizen_name", "").strip()

        checks: Dict[str, str] = {
            "required_fields": "PASSED",
            "name_format": "PASSED",
            "address_completeness": "PASSED",
            "date_format": "PASSED",
            "document_reference": "PASSED",
            "duplicate_check": "PASSED",
            "consent_validity": "PASSED",
        }
        errors: List[str] = []

        # 1. Required Fields Check
        if not citizen_name:
            checks["required_fields"] = "FAILED"
            errors.append("Required field 'citizen_name' is missing.")
        if not existing_addr or not new_addr:
            checks["required_fields"] = "FAILED"
            errors.append("Address structures ('existing_address' or 'new_address') are missing.")
        if not app_dict.get("consent_reference"):
            checks["required_fields"] = "FAILED"
            errors.append("Required field 'consent_reference' is missing.")

        # 2. Name Format Check (Synthetic names like 'Demo Citizen 001' or 'Rajesh Shantaram Patil' are valid)
        if citizen_name:
            if len(citizen_name) < 2 or len(citizen_name) > 100:
                checks["name_format"] = "FAILED"
                errors.append("Citizen name length must be between 2 and 100 characters.")
            elif not re.match(r"^[a-zA-Z0-9\s\.\,\'-]+$", citizen_name):
                checks["name_format"] = "FAILED"
                errors.append("Citizen name contains illegal special characters.")

        # 3. Address Completeness Check (House No, Street, Village, Taluka, District, Pincode)
        mandatory_addr_fields = ["house_no", "street", "village", "taluka", "district", "pincode"]
        for field in mandatory_addr_fields:
            val_new = str(new_addr.get(field, "")).strip()
            if not val_new or val_new.upper() in ("N/A", "EMPTY", "NULL", "NONE"):
                checks["address_completeness"] = "FAILED"
                errors.append(f"New address is incomplete: missing '{field}'.")
            elif re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", val_new):
                checks["address_completeness"] = "FAILED"
                errors.append(f"Address field '{field}' contains illegal control characters.")
            elif len(val_new) > 150:
                checks["address_completeness"] = "FAILED"
                errors.append(f"Address field '{field}' exceeds maximum length of 150 characters.")

        # Pincode format validation (6-digit Indian PIN) (SEC-09)
        pin_val = str(new_addr.get("pincode", "")).strip()
        if pin_val and not re.match(r"^[1-9][0-9]{5}$", pin_val):
            checks["address_completeness"] = "FAILED"
            errors.append(f"Invalid postal pincode '{pin_val}': must be a 6-digit number not starting with 0.")

        existing_pin = str(existing_addr.get("pincode", "")).strip()
        if existing_pin and not re.match(r"^[1-9][0-9]{5}$", existing_pin):
            checks["address_completeness"] = "FAILED"
            errors.append(f"Invalid existing address postal pincode '{existing_pin}': must be a 6-digit number not starting with 0.")

        # 4. Date Format Validation
        rec_at = app_dict.get("received_at")
        if not rec_at:
            checks["date_format"] = "WARNING"

        # 5. Document Reference Validation
        if not proof_docs or len(proof_docs) == 0:
            checks["document_reference"] = "FAILED"
            errors.append("No supporting address proof documents attached.")
        else:
            for doc in proof_docs:
                doc_id = doc.get("document_id", "")
                if not doc_id or len(doc_id) < 3:
                    checks["document_reference"] = "FAILED"
                    errors.append(f"Invalid document identifier: '{doc_id}'.")

        # 6. Duplicate Application Check
        if all_apps:
            corr_id = app_dict.get("correlation_id", "")
            cit_ref = app_dict.get("citizen_reference_id", "")
            srv = app_dict.get("service_type", "")
            for other in all_apps:
                if other.get("application_id") != app_id:
                    if (
                        other.get("correlation_id") == corr_id
                        or (other.get("citizen_reference_id") == cit_ref and other.get("service_type") == srv and other.get("status") in ("PENDING", "PROCESSING"))
                    ):
                        checks["duplicate_check"] = "FAILED"
                        errors.append(f"Duplicate application detected matching citizen reference '{cit_ref}' and service '{srv}'.")
                        break

        # 7. Consent Validity Check
        consent_res = ConsentService.validate_consent(app_dict)
        if not consent_res.valid:
            checks["consent_validity"] = "FAILED"
            errors.extend(consent_res.errors)

        is_valid = len(errors) == 0
        logger.info("Data validation for app '%s': valid=%s, errors=%d", app_id, is_valid, len(errors))

        return DataValidationResult(
            application_id=app_id,
            valid=is_valid,
            checks=checks,
            errors=errors,
        )
