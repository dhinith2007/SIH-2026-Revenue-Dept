from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Anchor base timestamp to now (UTC) for realistic relative dates
_NOW = datetime.now(timezone.utc)
_TODAY_START = _NOW.replace(hour=0, minute=0, second=0, microsecond=0)
_FUTURE_EXPIRY = _NOW + timedelta(days=365)
_PAST_EXPIRY = _NOW - timedelta(days=30)

SYNTHETIC_APPLICATIONS: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------------
    # DEMO CASE 1 (Primary Happy Path): Valid Consent, Valid Data, Valid Doc
    # ------------------------------------------------------------------------
    {
        "id": "APP-REV-001",
        "application_id": "GM-2026-000124",
        "correlation_id": "GM-CORR-2026-000124",
        "citizen_reference_id": "CIT-MH-1001",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "consent_reference": "GM-CONSENT-2026-000124",
        "priority": "HIGH",
        "status": "PENDING",
        "required_action": "Verify new residential address against Taluka land registry & electricity proof",
        "citizen_name": "Rajesh Shantaram Patil",
        "received_at": _TODAY_START + timedelta(hours=9, minutes=15),
        "updated_at": _TODAY_START + timedelta(hours=9, minutes=15),
        "processing_started_at": None,
        "completed_at": None,
        "assigned_officer_id": "USR-REV-001",
        "consent_record": {
            "status": "VALID",
            "purpose": "Update Revenue address record & 7/12 land registry linkage",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Rajesh Shantaram Patil",
            "existing_address": {
                "house_no": "Flat 201, Shanti Niketan",
                "street": "Prabhat Road, Lane 4",
                "village": "Deccan Gymkhana",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411004",
            },
            "new_address": {
                "house_no": "Flat 402, Shivshankar Heights",
                "street": "Karve Road",
                "village": "Kothrud",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411038",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-9081",
                    "document_type": "ELECTRICITY_BILL",
                    "document_name": "MSEDCL_Bill_July2026.pdf",
                    "extracted_name": "Rajesh Shantaram Patil",
                    "extracted_address": "Flat 402, Shivshankar Heights, Karve Road, Kothrud, Taluka: Haveli, Dist: Pune - 411038",
                    "upload_date": (_TODAY_START + timedelta(hours=9, minutes=10)).isoformat(),
                    "verification_status": "VALIDATED",
                    "file_size": "1.4 MB",
                }
            ],
            "remarks": "Citizen requested synchronization for agricultural land declaration.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=9, minutes=15)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            }
        ],
    },

    # ------------------------------------------------------------------------
    # DEMO CASE 2 (Expired Consent Block): Consent has expired
    # ------------------------------------------------------------------------
    {
        "id": "APP-REV-004",
        "application_id": "GM-2026-000127",
        "correlation_id": "CORR-2026-000127",
        "citizen_reference_id": "CIT-MH-1004",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Update Revenue address record & 7/12 land registry linkage",
        "consent_reference": "CONSENT-2026-00127",
        "priority": "HIGH",
        "status": "PENDING",
        "required_action": "Consent validation prerequisite check required",
        "citizen_name": "Sunita Sanjay Kulkarni",
        "received_at": _TODAY_START + timedelta(hours=8, minutes=0),
        "updated_at": _TODAY_START + timedelta(hours=8, minutes=0),
        "processing_started_at": None,
        "completed_at": None,
        "assigned_officer_id": None,
        "consent_record": {
            "status": "EXPIRED",
            "purpose": "Update Revenue address record",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _PAST_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Sunita Sanjay Kulkarni",
            "existing_address": {
                "house_no": "House 12",
                "street": "Bajar Peth",
                "village": "Wadgaon",
                "taluka": "Maval",
                "district": "Pune",
                "pincode": "412106",
            },
            "new_address": {
                "house_no": "House 89",
                "street": "Gandhi Chowk",
                "village": "Lonavala",
                "taluka": "Maval",
                "district": "Pune",
                "pincode": "410401",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-7102",
                    "document_type": "PROPERTY_TAX_RECEIPT",
                    "document_name": "Lonavala_Tax_Receipt.pdf",
                    "extracted_name": "Sunita Sanjay Kulkarni",
                    "extracted_address": "House 89, Gandhi Chowk, Lonavala, Taluka: Maval, Dist: Pune - 410401",
                    "upload_date": (_TODAY_START + timedelta(hours=7, minutes=55)).isoformat(),
                    "verification_status": "VALIDATED",
                    "file_size": "2.3 MB",
                }
            ],
            "remarks": "Citizen consent token expired prior to processing.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=8, minutes=0)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            }
        ],
    },

    # ------------------------------------------------------------------------
    # DEMO CASE 3 (Missing Document / Action Required): Needs Request Info
    # ------------------------------------------------------------------------
    {
        "id": "APP-REV-005",
        "application_id": "GM-2026-000128",
        "correlation_id": "CORR-2026-000128",
        "citizen_reference_id": "CIT-MH-1005",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address update for rural revenue boundary linkage",
        "consent_reference": "CONSENT-2026-00128",
        "priority": "HIGH",
        "status": "PROCESSING",
        "required_action": "Missing address proof document. Officer action needed to request document.",
        "citizen_name": "Vikram Harishchandra Jadhav",
        "received_at": _TODAY_START + timedelta(hours=7, minutes=15),
        "updated_at": _TODAY_START + timedelta(hours=9, minutes=0),
        "processing_started_at": _TODAY_START + timedelta(hours=9, minutes=0),
        "completed_at": None,
        "assigned_officer_id": "USR-REV-001",
        "consent_record": {
            "status": "VALID",
            "purpose": "Address update for rural revenue boundary linkage",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Vikram Harishchandra Jadhav",
            "existing_address": {
                "house_no": "Gat No. 204",
                "street": "Wadgaon Road",
                "village": "Khadkale",
                "taluka": "Maval",
                "district": "Pune",
                "pincode": "412106",
            },
            "new_address": {
                "house_no": "Plot 55",
                "street": "Station Road",
                "village": "Talegaon Dabhade",
                "taluka": "Maval",
                "district": "Pune",
                "pincode": "410506",
            },
            "proof_documents": [],  # Empty document list!
            "remarks": "Supporting document upload failed during citizen onboarding.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=7, minutes=15)).isoformat(),
                "notes": "Incoming Address Change payload ingested without proof attachment.",
            },
            {
                "step_name": "Desk Scrutiny Started",
                "actor": "Rajendra Mane (Revenue Officer)",
                "action": "PROCESSING_STARTED",
                "timestamp": (_TODAY_START + timedelta(hours=9, minutes=0)).isoformat(),
                "notes": "Officer initiated scrutiny.",
            }
        ],
    },

    # ------------------------------------------------------------------------
    # DEMO CASE 4 (Document Mismatch Rejection): Address on bill mismatches
    # ------------------------------------------------------------------------
    {
        "id": "APP-REV-006",
        "application_id": "GM-2026-000129",
        "correlation_id": "CORR-2026-000129",
        "citizen_reference_id": "CIT-MH-1006",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address update for property tax consolidation",
        "consent_reference": "CONSENT-2026-00129",
        "priority": "NORMAL",
        "status": "PROCESSING",
        "required_action": "Verify submitted utility proof against requested Taluka",
        "citizen_name": "Amol Dattatray Shinde",
        "received_at": _TODAY_START + timedelta(hours=6, minutes=45),
        "updated_at": _TODAY_START + timedelta(hours=8, minutes=30),
        "processing_started_at": _TODAY_START + timedelta(hours=8, minutes=30),
        "completed_at": None,
        "assigned_officer_id": "USR-REV-001",
        "consent_record": {
            "status": "VALID",
            "purpose": "Address update for property tax consolidation",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Amol Dattatray Shinde",
            "existing_address": {
                "house_no": "House 10",
                "street": "Main Road",
                "village": "Chakan",
                "taluka": "Khed",
                "district": "Pune",
                "pincode": "410501",
            },
            "new_address": {
                "house_no": "Gat 102",
                "street": "Urse MIDC",
                "village": "Urse",
                "taluka": "Maval",
                "district": "Pune",
                "pincode": "410506",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-5510",
                    "document_type": "ELECTRICITY_BILL",
                    "document_name": "Electricity_Bill_Mismatched.pdf",
                    "extracted_name": "Amol Dattatray Shinde",
                    "extracted_address": "Plot 99, Shivaji Nagar, Baramati City, Taluka: Baramati, Dist: Pune - 413102",
                    "upload_date": (_TODAY_START + timedelta(hours=6, minutes=40)).isoformat(),
                    "verification_status": "MISMATCH",
                    "file_size": "1.8 MB",
                }
            ],
            "remarks": "Address on uploaded MSEDCL bill is in Baramati, while requested new address is in Maval.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=6, minutes=45)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            },
            {
                "step_name": "Desk Scrutiny Started",
                "actor": "Rajendra Mane (Revenue Officer)",
                "action": "PROCESSING_STARTED",
                "timestamp": (_TODAY_START + timedelta(hours=8, minutes=30)).isoformat(),
                "notes": "Officer initiated scrutiny.",
            }
        ],
    },

    # ------------------------------------------------------------------------
    # DEMO CASE 5 (Incomplete Address Data): Missing village and taluka
    # ------------------------------------------------------------------------
    {
        "id": "APP-REV-007",
        "application_id": "GM-2026-000130",
        "correlation_id": "CORR-2026-000130",
        "citizen_reference_id": "CIT-MH-1007",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address update for municipal tax registry",
        "consent_reference": "CONSENT-2026-00130",
        "priority": "LOW",
        "status": "PENDING",
        "required_action": "Address completeness check",
        "citizen_name": "Kavita Suresh More",
        "received_at": _TODAY_START + timedelta(hours=6, minutes=0),
        "updated_at": _TODAY_START + timedelta(hours=6, minutes=0),
        "processing_started_at": None,
        "completed_at": None,
        "assigned_officer_id": None,
        "consent_record": {
            "status": "VALID",
            "purpose": "Address update for municipal tax registry",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Kavita Suresh More",
            "existing_address": {
                "house_no": "Flat 101",
                "street": "Shukrawar Peth",
                "village": "Pune City",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411002",
            },
            "new_address": {
                "house_no": "Plot 22",
                "street": "College Road",
                "village": "",  # MISSING VILLAGE!
                "taluka": "",   # MISSING TALUKA!
                "district": "Pune",
                "pincode": "411004",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-4421",
                    "document_type": "REGISTERED_RENT_AGREEMENT",
                    "document_name": "RentAgreement_Pune_2026.pdf",
                    "extracted_name": "Kavita Suresh More",
                    "extracted_address": "Plot 22, College Road, Pune - 411004",
                    "upload_date": (_TODAY_START + timedelta(hours=5, minutes=50)).isoformat(),
                    "verification_status": "PENDING",
                    "file_size": "2.9 MB",
                }
            ],
            "remarks": "Incomplete address submission.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=6, minutes=0)).isoformat(),
                "notes": "Payload ingested with incomplete geographical keys.",
            }
        ],
    },

    # ------------------------------------------------------------------------
    # DEMO CASE 6 (Already Finalized / Immutable): Status VERIFIED
    # ------------------------------------------------------------------------
    {
        "id": "APP-REV-008",
        "application_id": "GM-2026-000131",
        "correlation_id": "CORR-2026-000131",
        "citizen_reference_id": "CIT-MH-1008",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address update for 7/12 extract synchronization",
        "consent_reference": "CONSENT-2026-00131",
        "priority": "NORMAL",
        "status": "VERIFIED",
        "required_action": "Application verified & approved by Revenue Officer.",
        "citizen_name": "Deepak Raghunath Jagtap",
        "received_at": _TODAY_START - timedelta(days=1, hours=-10),
        "updated_at": _TODAY_START - timedelta(days=1, hours=-14),
        "processing_started_at": _TODAY_START - timedelta(days=1, hours=-11),
        "completed_at": _TODAY_START - timedelta(days=1, hours=-14),
        "assigned_officer_id": "USR-REV-001",
        "consent_record": {
            "status": "VALID",
            "purpose": "Address update for 7/12 extract synchronization",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Deepak Raghunath Jagtap",
            "existing_address": {
                "house_no": "House 4",
                "street": "Station Road",
                "village": "Daund City",
                "taluka": "Daund",
                "district": "Pune",
                "pincode": "413801",
            },
            "new_address": {
                "house_no": "Flat 303, Sai Residency",
                "street": "Hadapsar Bypass",
                "village": "Hadapsar",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411028",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-3310",
                    "document_type": "PROPERTY_TAX_RECEIPT",
                    "document_name": "Hadapsar_PropertyTax_2026.pdf",
                    "extracted_name": "Deepak Raghunath Jagtap",
                    "extracted_address": "Flat 303, Sai Residency, Hadapsar Bypass, Hadapsar, Taluka: Haveli, Dist: Pune - 411028",
                    "upload_date": (_TODAY_START - timedelta(days=1, hours=-10, minutes=10)).isoformat(),
                    "verification_status": "VERIFIED",
                    "file_size": "1.7 MB",
                }
            ],
            "remarks": "Approved after 7/12 extract verification.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START - timedelta(days=1, hours=-10)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            },
            {
                "step_name": "Revenue Officer Approval",
                "actor": "Rajendra Mane (Revenue Officer)",
                "action": "APPROVED",
                "timestamp": (_TODAY_START - timedelta(days=1, hours=-14)).isoformat(),
                "notes": "Address proof matches requested residence record and Taluka land registry.",
            }
        ],
    },

    # ------------------------------------------------------------------------
    # Additional Diverse Applications for Operational Realism
    # ------------------------------------------------------------------------
    {
        "id": "APP-REV-002",
        "application_id": "GM-2026-000125",
        "correlation_id": "CORR-2026-000125",
        "citizen_reference_id": "CIT-MH-1002",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Residence update for local tehsil record verification",
        "consent_reference": "CONSENT-2026-00125",
        "priority": "NORMAL",
        "status": "PROCESSING",
        "required_action": "Desk scrutiny of registered sale deed and village revenue register",
        "citizen_name": "Pooja Vijay Deshmukh",
        "received_at": _TODAY_START + timedelta(hours=7, minutes=30),
        "updated_at": _TODAY_START + timedelta(hours=10, minutes=0),
        "processing_started_at": _TODAY_START + timedelta(hours=8, minutes=45),
        "completed_at": None,
        "assigned_officer_id": "USR-REV-001",
        "consent_record": {
            "status": "VALID",
            "purpose": "Residence update for local tehsil record verification",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Pooja Vijay Deshmukh",
            "existing_address": {
                "house_no": "Old Quarter 14",
                "street": "Civil Lines",
                "village": "Nagpur Urban",
                "taluka": "Nagpur",
                "district": "Nagpur",
                "pincode": "440001",
            },
            "new_address": {
                "house_no": "Plot 12B, Yashoda Villa",
                "street": "Samarth Nagar",
                "village": "Nagpur Urban",
                "taluka": "Nagpur",
                "district": "Nagpur",
                "pincode": "440010",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-8821",
                    "document_type": "REGISTERED_SALE_DEED",
                    "document_name": "SaleDeed_Nagpur_2026.pdf",
                    "extracted_name": "Pooja Vijay Deshmukh",
                    "extracted_address": "Plot 12B, Yashoda Villa, Samarth Nagar, Nagpur Urban, Taluka: Nagpur, Dist: Nagpur - 440010",
                    "upload_date": (_TODAY_START + timedelta(hours=7, minutes=25)).isoformat(),
                    "verification_status": "VALIDATED",
                    "file_size": "4.1 MB",
                }
            ],
            "remarks": "Change of residence following property purchase.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=7, minutes=30)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            }
        ],
    },

    {
        "id": "APP-REV-003",
        "application_id": "GM-2026-000126",
        "correlation_id": "CORR-2026-000126",
        "citizen_reference_id": "CIT-MH-1003",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address record synchronization for taluka boundary verification",
        "consent_reference": "CONSENT-2026-00126",
        "priority": "HIGH",
        "status": "ACTION_REQUIRED",
        "required_action": "Citizen Action Required (NEW_DOCUMENT): Please upload municipal electricity bill for Nashik residence.",
        "citizen_name": "Anand Mohan Shinde",
        "received_at": _NOW - timedelta(days=2, hours=4),
        "updated_at": _NOW - timedelta(days=1, hours=2),
        "processing_started_at": _NOW - timedelta(days=2, hours=1),
        "completed_at": None,
        "assigned_officer_id": "USR-REV-002",
        "consent_record": {
            "status": "VALID",
            "purpose": "Address record synchronization",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Anand Mohan Shinde",
            "existing_address": {
                "house_no": "House 55",
                "street": "Panchavati Marg",
                "village": "Panchavati",
                "taluka": "Nashik",
                "district": "Nashik",
                "pincode": "422003",
            },
            "new_address": {
                "house_no": "B-14, Shanti Nagar",
                "street": "Station Road",
                "village": "Nashik City",
                "taluka": "Nashik",
                "district": "Nashik",
                "pincode": "422001",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-7910",
                    "document_type": "ELECTRICITY_BILL",
                    "document_name": "Nashik_Electricity_Old.pdf",
                    "extracted_name": "Anand Mohan Shinde",
                    "extracted_address": "House 55, Panchavati, Nashik - 422003",
                    "upload_date": (_NOW - timedelta(days=2, hours=4)).isoformat(),
                    "verification_status": "ACTION_REQUIRED",
                    "file_size": "1.1 MB",
                }
            ],
            "remarks": "Uploaded bill corresponds to previous residence.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_NOW - timedelta(days=2, hours=4)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            },
            {
                "step_name": "Department Query Raised",
                "actor": "Sunil Kadam (Senior Officer)",
                "action": "INFORMATION_REQUESTED",
                "timestamp": (_NOW - timedelta(days=1, hours=2)).isoformat(),
                "notes": "Please upload municipal electricity bill for Nashik residence.",
            }
        ],
    },

    {
        "id": "APP-REV-009",
        "application_id": "GM-2026-000132",
        "correlation_id": "CORR-2026-000132",
        "citizen_reference_id": "CIT-MH-1009",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address update for 7/12 land records",
        "consent_reference": "CONSENT-2026-00132",
        "priority": "HIGH",
        "status": "PENDING",
        "required_action": "Verify new residence against Baramati Tehsil land map",
        "citizen_name": "Suresh Balkrishna Pawar",
        "received_at": _TODAY_START + timedelta(hours=5, minutes=30),
        "updated_at": _TODAY_START + timedelta(hours=5, minutes=30),
        "processing_started_at": None,
        "completed_at": None,
        "assigned_officer_id": None,
        "consent_record": {
            "status": "VALID",
            "purpose": "Address update for 7/12 land records",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Suresh Balkrishna Pawar",
            "existing_address": {
                "house_no": "Gat 45",
                "street": "Malegaon Road",
                "village": "Malegaon Khurd",
                "taluka": "Baramati",
                "district": "Pune",
                "pincode": "413115",
            },
            "new_address": {
                "house_no": "Bunglow 8",
                "street": "Vidyanagari",
                "village": "Baramati City",
                "taluka": "Baramati",
                "district": "Pune",
                "pincode": "413133",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-2201",
                    "document_type": "PROPERTY_TAX_RECEIPT",
                    "document_name": "Baramati_Tax_2026.pdf",
                    "extracted_name": "Suresh Balkrishna Pawar",
                    "extracted_address": "Bunglow 8, Vidyanagari, Baramati City, Taluka: Baramati, Dist: Pune - 413133",
                    "upload_date": (_TODAY_START + timedelta(hours=5, minutes=20)).isoformat(),
                    "verification_status": "VALIDATED",
                    "file_size": "2.4 MB",
                }
            ],
            "remarks": "Relocation within Baramati jurisdiction.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=5, minutes=30)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            }
        ],
    },

    {
        "id": "APP-REV-010",
        "application_id": "GM-2026-000133",
        "correlation_id": "CORR-2026-000133",
        "citizen_reference_id": "CIT-MH-1010",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Residence update for Taluka agriculture subsidy linkage",
        "consent_reference": "CONSENT-2026-00133",
        "priority": "URGENT",
        "status": "PROCESSING",
        "required_action": "Expedited verification of agricultural residential declaration",
        "citizen_name": "Meena Chandrakant Bhosale",
        "received_at": _TODAY_START + timedelta(hours=4, minutes=45),
        "updated_at": _TODAY_START + timedelta(hours=7, minutes=10),
        "processing_started_at": _TODAY_START + timedelta(hours=6, minutes=30),
        "completed_at": None,
        "assigned_officer_id": "USR-REV-001",
        "consent_record": {
            "status": "VALID",
            "purpose": "Residence update for Taluka agriculture subsidy linkage",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Meena Chandrakant Bhosale",
            "existing_address": {
                "house_no": "House 18",
                "street": "Bajar Peth",
                "village": "Shikrapur",
                "taluka": "Shirur",
                "district": "Pune",
                "pincode": "412208",
            },
            "new_address": {
                "house_no": "Gat No. 312",
                "street": "Koregaon Road",
                "village": "Koregaon Bhima",
                "taluka": "Shirur",
                "district": "Pune",
                "pincode": "412216",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-1190",
                    "document_type": "ELECTRICITY_BILL",
                    "document_name": "MSEDCL_Shirur_2026.pdf",
                    "extracted_name": "Meena Chandrakant Bhosale",
                    "extracted_address": "Gat No. 312, Koregaon Road, Koregaon Bhima, Taluka: Shirur, Dist: Pune - 412216",
                    "upload_date": (_TODAY_START + timedelta(hours=4, minutes=40)).isoformat(),
                    "verification_status": "VALIDATED",
                    "file_size": "1.3 MB",
                }
            ],
            "remarks": "Urgent agricultural subsidy deadline.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=4, minutes=45)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            },
            {
                "step_name": "Desk Scrutiny Started",
                "actor": "Rajendra Mane (Revenue Officer)",
                "action": "PROCESSING_STARTED",
                "timestamp": (_TODAY_START + timedelta(hours=6, minutes=30)).isoformat(),
                "notes": "Expedited processing initiated.",
            }
        ],
    },

    {
        "id": "APP-REV-011",
        "application_id": "GM-2026-000134",
        "correlation_id": "CORR-2026-000134",
        "citizen_reference_id": "CIT-MH-1011",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address update for tehsil record synchronization",
        "consent_reference": "CONSENT-2026-00134",
        "priority": "LOW",
        "status": "VERIFIED",
        "required_action": "Application verified & approved by Revenue Officer.",
        "citizen_name": "Nitin Vasantrao Gaikwad",
        "received_at": _NOW - timedelta(days=3, hours=5),
        "updated_at": _NOW - timedelta(days=3, hours=1),
        "processing_started_at": _NOW - timedelta(days=3, hours=4),
        "completed_at": _NOW - timedelta(days=3, hours=1),
        "assigned_officer_id": "USR-REV-001",
        "consent_record": {
            "status": "VALID",
            "purpose": "Address update for tehsil record synchronization",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Nitin Vasantrao Gaikwad",
            "existing_address": {
                "house_no": "Old Quarter 5",
                "street": "Shaniwar Wada",
                "village": "Pune City",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411030",
            },
            "new_address": {
                "house_no": "Flat 502, Ganga Heights",
                "street": "Sinhagad Road",
                "village": "Vadgaon Budruk",
                "taluka": "Haveli",
                "district": "Pune",
                "pincode": "411041",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-0988",
                    "document_type": "PROPERTY_TAX_RECEIPT",
                    "document_name": "PMC_Tax_Receipt.pdf",
                    "extracted_name": "Nitin Vasantrao Gaikwad",
                    "extracted_address": "Flat 502, Ganga Heights, Sinhagad Road, Vadgaon Budruk, Taluka: Haveli, Dist: Pune - 411041",
                    "upload_date": (_NOW - timedelta(days=3, hours=5)).isoformat(),
                    "verification_status": "VERIFIED",
                    "file_size": "2.1 MB",
                }
            ],
            "remarks": "Completed successfully.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_NOW - timedelta(days=3, hours=5)).isoformat(),
                "notes": "Incoming Address Change payload ingested via REST contract.",
            },
            {
                "step_name": "Revenue Officer Approval",
                "actor": "Rajendra Mane (Revenue Officer)",
                "action": "APPROVED",
                "timestamp": (_NOW - timedelta(days=3, hours=1)).isoformat(),
                "notes": "Address matched PMC property registry.",
            }
        ],
    },

    {
        "id": "APP-REV-012",
        "application_id": "GM-2026-000135",
        "correlation_id": "CORR-2026-000135",
        "citizen_reference_id": "CIT-MH-1012",
        "service_type": "ADDRESS_CHANGE",
        "requested_operation": "UPDATE_REVENUE_ADDRESS",
        "purpose": "Address update for Taluka revenue boundary record",
        "consent_reference": "CONSENT-2026-00135",
        "priority": "NORMAL",
        "status": "QUEUED",
        "required_action": "Awaiting initial intake pipeline processing",
        "citizen_name": "Pranali Ramesh Tawde",
        "received_at": _TODAY_START + timedelta(hours=3, minutes=15),
        "updated_at": _TODAY_START + timedelta(hours=3, minutes=15),
        "processing_started_at": None,
        "completed_at": None,
        "assigned_officer_id": None,
        "consent_record": {
            "status": "VALID",
            "purpose": "Address update for Taluka revenue boundary record",
            "data_scope": "address.change",
            "recipient": "Revenue & Forest Department",
            "expires_at": _FUTURE_EXPIRY,
            "revoked_at": None,
        },
        "data_payload": {
            "citizen_name": "Pranali Ramesh Tawde",
            "existing_address": {
                "house_no": "House 102",
                "street": "Somwar Peth",
                "village": "Satara City",
                "taluka": "Satara",
                "district": "Satara",
                "pincode": "415002",
            },
            "new_address": {
                "house_no": "Bunglow 4",
                "street": "Panchgani Road",
                "village": "Wai",
                "taluka": "Wai",
                "district": "Satara",
                "pincode": "412803",
            },
            "proof_documents": [
                {
                    "document_id": "DOC-REV-0129",
                    "document_type": "ELECTRICITY_BILL",
                    "document_name": "Wai_Electricity_2026.pdf",
                    "extracted_name": "Pranali Ramesh Tawde",
                    "extracted_address": "Bunglow 4, Panchgani Road, Wai, Taluka: Wai, Dist: Satara - 412803",
                    "upload_date": (_TODAY_START + timedelta(hours=3, minutes=10)).isoformat(),
                    "verification_status": "PENDING",
                    "file_size": "1.6 MB",
                }
            ],
            "remarks": "Queued in buffer intake pool.",
        },
        "workflow_history": [
            {
                "step_name": "GovMesh Intake",
                "actor": "Citizen (via GovMesh Channel)",
                "action": "APPLICATION_RECEIVED",
                "timestamp": (_TODAY_START + timedelta(hours=3, minutes=15)).isoformat(),
                "notes": "Incoming Address Change payload queued in buffer.",
            }
        ],
    },
]


def get_seeded_applications() -> List[Dict[str, Any]]:
    """Returns synthetic applications with fresh timestamps."""
    return SYNTHETIC_APPLICATIONS


# Backward compatibility alias
DEMO_APPLICATIONS = SYNTHETIC_APPLICATIONS
