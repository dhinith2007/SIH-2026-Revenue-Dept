from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, status
from fastapi.responses import JSONResponse, Response
from app.schemas.common import BaseResponse
from app.schemas.workflow import (
    ProofDocumentMetadata,
    DocumentUploadResponse,
    DocumentVerificationResult,
    DocumentOverrideRequest,
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.audit_repository import AuditRepository
from app.services.document_verification_service import DocumentVerificationService
from app.api.deps import (
    get_application_repository,
    get_audit_repository,
    get_current_user,
    require_permission,
)
from app.core.permissions import PermissionEnum
from app.core.errors import (
    ResourceNotFoundError,
    DocumentTypeUnsupportedError,
    DocumentTooLargeError,
    DocumentEmptyError,
    DocumentInvalidError,
    ApplicationFinalizedError,
)
from app.core.simulation import check_simulated_failure
from app.core.logging import logger

router = APIRouter()

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
}


@router.post(
    "/revenue/application/{application_id}/documents",
    response_model=BaseResponse[DocumentUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Attach Proof Document",
    description="Validates file type (PDF, JPG, PNG) and file size (max 10MB) before attaching to application.",
)
async def upload_document_endpoint(
    request: Request,
    application_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("ELECTRICITY_BILL"),
    app_repo: ApplicationRepository = Depends(get_application_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.DOCUMENT_VERIFY)),
):
    await check_simulated_failure(request, correlation_id=application_id)
    app = app_repo.get_by_application_id(application_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

    if app.get("status") in ("VERIFIED", "REJECTED"):
        raise ApplicationFinalizedError(
            message="Cannot upload new documents to a finalized immutable application."
        )

    # 1. Validate File MIME Type
    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES and not any(file.filename.lower().endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png"]):
        raise DocumentTypeUnsupportedError(
            message=f"Unsupported file format '{mime}'. Supported formats: PDF, JPG, PNG."
        )

    # 2. Read and validate file content
    content = await file.read()
    file_size_bytes = len(content)

    if file_size_bytes == 0:
        raise DocumentEmptyError(message="Uploaded file is empty (0 bytes).")

    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        raise DocumentTooLargeError(
            message=f"File size ({file_size_bytes / (1024 * 1024):.1f} MB) exceeds maximum allowed 10 MB."
        )

    # 3. Create document record
    doc_id = f"DOC-REV-{uuid.uuid4().hex[:6].upper()}"
    size_str = f"{file_size_bytes / 1024:.1f} KB" if file_size_bytes < 1024 * 1024 else f"{file_size_bytes / (1024 * 1024):.1f} MB"

    doc_dict = {
        "document_id": doc_id,
        "document_name": file.filename or "Uploaded_Document.pdf",
        "document_type": document_type,
        "mime_type": mime,
        "file_size": size_str,
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "verification_status": "PENDING",
        "extracted_name": app.get("citizen_name"),
    }

    app_repo.attach_document(application_id, doc_dict)

    # 4. Audit Trail
    audit_repo.record_audit_event(
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
        application_id=application_id,
        action="DOCUMENT_UPLOADED",
        previous_status=app.get("status"),
        new_status=app.get("status", "PROCESSING"),
        reason=f"Attached proof document: {doc_dict['document_name']} ({doc_id})",
        correlation_id=app.get("correlation_id", application_id),
        details={"document_id": doc_id, "document_type": document_type, "file_size": size_str},
    )

    logger.info("Document '%s' uploaded for application '%s' by '%s'", doc_id, application_id, current_user["username"])

    return BaseResponse(
        success=True,
        data=DocumentUploadResponse(
            document_id=doc_id,
            application_id=application_id,
            document_name=doc_dict["document_name"],
            document_type=document_type,
            file_size=size_str,
            mime_type=mime,
            verification_status="PENDING",
            message="Document uploaded and attached successfully.",
        ),
        message=f"Document '{doc_id}' uploaded and attached successfully.",
    )


@router.get(
    "/revenue/application/{application_id}/documents",
    response_model=BaseResponse[List[ProofDocumentMetadata]],
    status_code=status.HTTP_200_OK,
    summary="List Application Attached Documents",
)
async def list_application_documents_endpoint(
    request: Request,
    application_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id=application_id)
    app = app_repo.get_by_application_id(application_id)
    if not app:
        raise ResourceNotFoundError(message=f"Application '{application_id}' not found.")

    data_payload = app.get("data_payload", {})
    proof_docs = data_payload.get("proof_documents", [])

    results = []
    for idx, doc in enumerate(proof_docs):
        ver_res = DocumentVerificationService.verify_document(app, doc_index=idx)
        results.append(
            ProofDocumentMetadata(
                document_id=doc.get("document_id", "DOC-UNKNOWN"),
                application_id=application_id,
                document_name=doc.get("document_name", "Document.pdf"),
                document_type=doc.get("document_type", "ELECTRICITY_BILL"),
                mime_type=doc.get("mime_type", "application/pdf"),
                file_size=doc.get("file_size", "1.2 MB"),
                upload_date=doc.get("upload_date"),
                verification_status=doc.get("verification_status", "PENDING"),
                extracted_name=doc.get("extracted_name"),
                extracted_address=doc.get("extracted_address"),
                verification_result=ver_res,
            )
        )

    return BaseResponse(
        success=True,
        data=results,
        message=f"Retrieved {len(results)} attached proof document(s).",
    )


@router.get(
    "/revenue/document/{document_id}",
    response_model=BaseResponse[ProofDocumentMetadata],
    status_code=status.HTTP_200_OK,
    summary="Get Document Metadata & Verification State",
)
async def get_document_endpoint(
    request: Request,
    document_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id=document_id)
    found = app_repo.get_document_by_id(document_id)
    if not found:
        raise ResourceNotFoundError(message=f"Document '{document_id}' not found.")

    doc, app = found
    data_payload = app.get("data_payload", {})
    proof_docs = data_payload.get("proof_documents", [])
    doc_index = 0
    for i, d in enumerate(proof_docs):
        if d.get("document_id") == document_id:
            doc_index = i
            break

    ver_res = DocumentVerificationService.verify_document(app, doc_index=doc_index)

    return BaseResponse(
        success=True,
        data=ProofDocumentMetadata(
            document_id=document_id,
            application_id=app.get("application_id"),
            document_name=doc.get("document_name", "Document.pdf"),
            document_type=doc.get("document_type", "ELECTRICITY_BILL"),
            mime_type=doc.get("mime_type", "application/pdf"),
            file_size=doc.get("file_size", "1.2 MB"),
            upload_date=doc.get("upload_date"),
            verification_status=doc.get("verification_status", "PENDING"),
            extracted_name=doc.get("extracted_name"),
            extracted_address=doc.get("extracted_address"),
            verification_result=ver_res,
        ),
        message=f"Retrieved document metadata for '{document_id}'.",
    )


@router.get(
    "/revenue/document/{document_id}/preview",
    summary="Safe Read-Only Document Preview",
    description="Returns simulated document preview binary / SVG visualization without exposing server paths.",
)
async def preview_document_endpoint(
    request: Request,
    document_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await check_simulated_failure(request, correlation_id=document_id)
    found = app_repo.get_document_by_id(document_id)
    if not found:
        raise ResourceNotFoundError(message=f"Document '{document_id}' not found.")

    doc, app = found
    citizen_name = app.get("citizen_name", "Citizen")
    doc_name = doc.get("document_name", "Utility_Bill.pdf")
    doc_type = doc.get("document_type", "ELECTRICITY_BILL").replace("_", " ")
    data_payload = app.get("data_payload", {})
    new_addr = data_payload.get("new_address", {})
    addr_str = f"{new_addr.get('house_no', '')}, {new_addr.get('street', '')}, {new_addr.get('village', '')}, Taluka: {new_addr.get('taluka', '')}, Dist: {new_addr.get('district', '')} - {new_addr.get('pincode', '')}"

    # Return clean SVG simulated document representation
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="100%" height="100%">
  <rect width="600" height="800" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <rect x="20" y="20" width="560" height="60" fill="#1e293b" rx="4"/>
  <text x="300" y="45" fill="#f8fafc" font-size="14" font-weight="bold" text-anchor="middle" font-family="sans-serif">MAHARASHTRA STATE ELECTRICITY DISTRIBUTION CO. LTD.</text>
  <text x="300" y="65" fill="#cbd5e1" font-size="11" text-anchor="middle" font-family="sans-serif">MUNICIPAL UTILITY CONSUMER STATEMENT • {doc_type}</text>
  
  <rect x="20" y="90" width="560" height="70" fill="#f8fafc" stroke="#e2e8f0" rx="4"/>
  <text x="40" y="115" fill="#64748b" font-size="10" font-family="sans-serif">CONSUMER NAME:</text>
  <text x="40" y="135" fill="#0f172a" font-size="13" font-weight="bold" font-family="sans-serif">{citizen_name}</text>
  <text x="340" y="115" fill="#64748b" font-size="10" font-family="sans-serif">DOCUMENT REF / ID:</text>
  <text x="340" y="135" fill="#0284c7" font-size="12" font-family="monospace">{document_id}</text>

  <rect x="20" y="170" width="560" height="120" fill="#f1f5f9" stroke="#e2e8f0" rx="4"/>
  <text x="40" y="195" fill="#64748b" font-size="10" font-family="sans-serif">REGISTERED PREMISES ADDRESS:</text>
  <text x="40" y="220" fill="#0f172a" font-size="12" font-weight="600" font-family="sans-serif">{addr_str}</text>
  <text x="40" y="250" fill="#64748b" font-size="10" font-family="sans-serif">TALUKA / JURISDICTION: <tspan fill="#0f172a" font-weight="bold">{new_addr.get('taluka', 'Haveli')}</tspan> | DISTRICT: <tspan fill="#0f172a" font-weight="bold">{new_addr.get('district', 'Pune')}</tspan></text>
  <text x="40" y="275" fill="#64748b" font-size="10" font-family="sans-serif">POSTAL PINCODE: <tspan fill="#0f172a" font-weight="bold">{new_addr.get('pincode', '411038')}</tspan></text>

  <rect x="20" y="300" width="560" height="400" fill="#ffffff" stroke="#e2e8f0" rx="4"/>
  <text x="40" y="330" fill="#94a3b8" font-size="11" font-weight="bold" font-family="sans-serif">OFFICIAL BILLING &amp; METER PARTICULARS</text>
  <line x1="40" y1="340" x2="560" y2="340" stroke="#e2e8f0" stroke-width="1"/>
  
  <text x="40" y="370" fill="#64748b" font-size="11" font-family="sans-serif">Tariff Category: LT-1 Residential</text>
  <text x="340" y="370" fill="#64748b" font-size="11" font-family="sans-serif">Meter Status: NORMAL (ACTIVE)</text>
  <text x="40" y="405" fill="#64748b" font-size="11" font-family="sans-serif">Sanctioned Load: 3.00 KW</text>
  <text x="340" y="405" fill="#64748b" font-size="11" font-family="sans-serif">Phase: Single Phase</text>
  <text x="40" y="440" fill="#64748b" font-size="11" font-family="sans-serif">Billing Cycle: Monthly</text>
  <text x="340" y="440" fill="#64748b" font-size="11" font-family="sans-serif">Payment Status: CLEARED</text>

  <rect x="40" y="620" width="520" height="60" fill="#f8fafc" stroke="#cbd5e1" stroke-dasharray="4" rx="4"/>
  <text x="300" y="645" fill="#64748b" font-size="10" font-family="sans-serif" text-anchor="middle">GOVMESH PROTOTYPE • SIMULATED RESIDENCE PROOF RECORD</text>
  <text x="300" y="665" fill="#94a3b8" font-size="9" font-family="sans-serif" text-anchor="middle">For Internal Departmental Verification Assistance Only • {doc_name}</text>
</svg>"""

    return Response(content=svg_content, media_type="image/svg+xml")


@router.post(
    "/revenue/document/{document_id}/verify",
    response_model=BaseResponse[DocumentVerificationResult],
    status_code=status.HTTP_200_OK,
    summary="Execute OCR & 6-Part Address Verification on Document",
)
async def verify_document_by_id_endpoint(
    request: Request,
    document_id: str,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.DOCUMENT_VERIFY)),
):
    await check_simulated_failure(request, correlation_id=document_id)
    found = app_repo.get_document_by_id(document_id)
    if not found:
        raise ResourceNotFoundError(message=f"Document '{document_id}' not found.")

    doc, app = found
    data_payload = app.get("data_payload", {})
    proof_docs = data_payload.get("proof_documents", [])
    doc_index = 0
    for i, d in enumerate(proof_docs):
        if d.get("document_id") == document_id:
            doc_index = i
            break

    result = DocumentVerificationService.verify_document(app, doc_index=doc_index)

    # Record Audit Event
    audit_action = "DOCUMENT_VERIFIED" if result.valid else ("DOCUMENT_MISMATCH" if result.match_status == "MISMATCH" else "OCR_COMPLETED")
    audit_repo.record_audit_event(
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
        application_id=app.get("application_id", ""),
        action=audit_action,
        previous_status=app.get("status"),
        new_status=app.get("status", "PROCESSING"),
        reason=f"OCR Verification result: {result.match_status} (Assistive Score: {result.assistive_score * 100:.0f}%)",
        correlation_id=app.get("correlation_id", document_id),
        details={
            "document_id": document_id,
            "match_status": result.match_status,
            "assistive_score": result.assistive_score,
            "matched_components": result.matched_components_count,
        },
    )

    return BaseResponse(
        success=True,
        data=result,
        message=f"Document verification complete: {result.match_status} ({result.explanation})",
    )


@router.post(
    "/revenue/document/{document_id}/override",
    response_model=BaseResponse[DocumentVerificationResult],
    status_code=status.HTTP_200_OK,
    summary="Officer Manual Override of OCR Recommendation",
    description="Records an authoritative manual override by a Revenue Officer with mandatory reason.",
)
async def override_document_endpoint(
    request: Request,
    document_id: str,
    payload: DocumentOverrideRequest,
    app_repo: ApplicationRepository = Depends(get_application_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    current_user: Dict[str, Any] = Depends(require_permission(PermissionEnum.DOCUMENT_VERIFY)),
):
    await check_simulated_failure(request, correlation_id=document_id)
    found = app_repo.get_document_by_id(document_id)
    if not found:
        raise ResourceNotFoundError(message=f"Document '{document_id}' not found.")

    doc, app = found
    app_id = app.get("application_id", "")

    if app.get("status") in ("VERIFIED", "REJECTED"):
        raise ApplicationFinalizedError(
            message="Cannot override document verification on a finalized immutable application."
        )

    override_data = {
        "officer_id": current_user["id"],
        "officer_name": current_user.get("full_name", current_user["username"]),
        "original_status": doc.get("verification_status", "PENDING"),
        "decision": payload.decision,
        "reason": payload.reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    app_repo.override_document(app_id, document_id, override_data)

    # Record Audit Event
    audit_repo.record_audit_event(
        officer_id=current_user["id"],
        officer_name=current_user.get("full_name", current_user["username"]),
        application_id=app_id,
        action="MANUAL_OVERRIDE",
        previous_status=app.get("status"),
        new_status=app.get("status", "PROCESSING"),
        reason=f"Officer manual override: {payload.decision} — {payload.reason}",
        correlation_id=app.get("correlation_id", app_id),
        details={"document_id": document_id, "override": override_data},
    )

    # Re-run verification with updated status
    found = app_repo.get_document_by_id(document_id)
    doc, app = found
    data_payload = app.get("data_payload", {})
    proof_docs = data_payload.get("proof_documents", [])
    doc_index = 0
    for i, d in enumerate(proof_docs):
        if d.get("document_id") == document_id:
            doc_index = i
            break

    result = DocumentVerificationService.verify_document(app, doc_index=doc_index)

    return BaseResponse(
        success=True,
        data=result,
        message=f"Manual override recorded: Document '{document_id}' set to '{payload.decision}'.",
    )
