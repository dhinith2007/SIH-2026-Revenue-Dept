# GOVMESH REVENUE & FOREST DEPARTMENT API

**Project:** GovMesh — SIH26129  
**Module:** Revenue & Forest Department of Maharashtra (Department 1)  
**Base Production URL:** `https://sih-2026-revenue-dept.onrender.com`  
**Frontend Application URL:** `https://sih-2026-revenue-dept.vercel.app`  
**API Prefix:** `/api/v1` (Mount aliases: `/api`, `/v1`, and root `/`)  
**Specification Standard:** OpenAPI 3.1.0 / FastAPI  

---

## TABLE OF CONTENTS
1. [Architecture & Protocol Overview](#architecture--protocol-overview)
2. [Authentication & RBAC Security Model](#authentication--rbac-security-model)
3. [Health & System Discovery Endpoints](#1-health--system-discovery-endpoints)
4. [Authentication & Session Endpoints](#2-authentication--session-endpoints)
5. [Administration & Personnel Management Endpoints](#3-administration--personnel-management-endpoints)
6. [Application Ingestion & Operational Queue Endpoints](#4-application-ingestion--operational-queue-endpoints)
7. [Revenue Address Verification Workflow Endpoints](#5-revenue-address-verification-workflow-endpoints)
8. [Proof Documents & OCR Verification Endpoints](#6-proof-documents--ocr-verification-endpoints)
9. [Departmental Notifications Endpoints](#7-departmental-notifications-endpoints)
10. [Audit Trail & Simulation Control Endpoints](#8-audit-trail--simulation-control-endpoints)
11. [Production API Status Table](#production-api-status)
12. [Missing / Broken Revenue APIs Report](#missing--broken-revenue-apis)

---

## ARCHITECTURE & PROTOCOL OVERVIEW

The Revenue & Forest Department backend operates as an independent departmental node in the GovMesh architecture. It processes citizen address updates against Taluka land records, validates DPDP statutory consent, verifies electricity and utility proof documents via 6-part address matching, and manages immutable state transitions with complete cryptographic audit logging.

```
+-------------------------------------------------------------------------------+
| FRONTEND: https://sih-2026-revenue-dept.vercel.app                            |
| (Vite SPA - React 18, Tailwind CSS, TypeScript, Client-Side RBAC Guard)       |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼ VITE_API_URL
+-------------------------------------------------------------------------------+
| BACKEND: https://sih-2026-revenue-dept.onrender.com                           |
| (FastAPI Application Server, Uvicorn ASGI, Python 3.11)                       |
+-------------------------------------------------------------------------------+
         │                                   │                      │
         ▼                                   ▼                      ▼
+──────────────────+               +───────────────────+   +──────────────────+
| AUTH / RBAC DEPS |               | WORKFLOW ENGINES  |   | DOCUMENT & OCR   |
| (JWT Bearer Auth,|               | (Consent, Address,|   | (Simulated OCR,  |
|  Role Evaluation)|               |  Status Machine)  |   |  Override Desk)  |
+------------------+               +-------------------+   +------------------+
         │                                   │                      │
         └─────────────────┬─────────────────┴──────────────────────┘
                           ▼
+-------------------------------------------------------------------------------+
| PERSISTENCE & DATA LAYER                                                      |
| (PostgreSQL Database with High-Resilience Serverless Memory / Seed Fallback)  |
+-------------------------------------------------------------------------------+
```

---

## AUTHENTICATION & RBAC SECURITY MODEL

All secured endpoints require an HTTP `Authorization` header containing an HMAC-SHA256 signed JSON Web Token (JWT):
```http
Authorization: Bearer <access_token>
```

### Departmental Roles & Hierarchy
1. **`DEPARTMENT_ADMINISTRATOR`**: Full administrative access, personnel management (`USER_MANAGE`), metadata configuration, system health monitoring.
2. **`SENIOR_REVENUE_OFFICER` (Tahsildar)**: Full operational scrutiny, application approval (`APPLICATION_APPROVE`), application rejection (`APPLICATION_REJECT`), manual OCR override (`EXCEPTION_OVERRIDE`), information requests, escalated case reviews.
3. **`REVENUE_OFFICER` (Taluka Scrutiny Officer)**: Application intake, scrutiny start, consent verification, address data validation, document proof verification, standard approvals and rejections.
4. **`READ_ONLY_AUDITOR`**: Read-only oversight across all applications and audit trail logs (`AUDIT_VIEW`).

---

## 1. HEALTH & SYSTEM DISCOVERY ENDPOINTS

### GET `/health`
#### Description
Root infrastructure health check returning service operational status, environment name, and software version.
#### Authentication
Not Required
#### Role / Permission
Public
#### Request
- **Headers:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Body:** None
#### Response
```json
{
  "status": "ok",
  "service": "revenue-department",
  "environment": "production",
  "version": "0.2.0",
  "timestamp": "2026-08-30T17:13:45.000Z"
}
```
#### Error Codes
- `503 Service Unavailable`: Critical runtime failure

---

### GET `/health/db`
#### Description
PostgreSQL database connectivity check and query latency measurement.
#### Authentication
Not Required
#### Role / Permission
Public
#### Request
- **Headers:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Body:** None
#### Response
```json
{
  "status": "connected",
  "database": "PostgreSQL",
  "latency_ms": 1.4,
  "error": null
}
```
*(Note: When PostgreSQL is unreachable in disconnected serverless mode, status reports `disconnected` and latency is measured without crashing the process).*
#### Error Codes
- None (Gracefully returns health telemetry)

---

### GET `/api/v1/revenue/system-info`
#### Description
Returns departmental metadata, project identifiers, and GovMesh interoperability specifications.
#### Authentication
Not Required
#### Role / Permission
Public
#### Request
- **Headers:** None
- **Path Parameters:** None
- **Query Parameters:** None
- **Body:** None
#### Response
```json
{
  "success": true,
  "data": {
    "department": "Revenue & Forest Department",
    "sub_department": "Land Records & Citizen Revenue Services",
    "state": "Maharashtra",
    "project_code": "SIH26129",
    "architecture_role": "Independent Department System (Department 1)",
    "current_phase": "Phase 06 - Document Verification & Ingestion",
    "simulated": true,
    "status": "STANDALONE_READY"
  },
  "message": "Revenue Department system information retrieved successfully."
}
```

---

## 2. AUTHENTICATION & SESSION ENDPOINTS

### POST `/api/v1/auth/login`
#### Description
Authenticates a departmental officer using Username, Email, or Mobile and Password, issuing a Bearer JWT.
#### Authentication
Not Required
#### Role / Permission
Public
#### Request
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "identifier": "revenue.officer",
  "password": "Officer@2026"
}
```
#### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "USR-REV-001",
    "username": "revenue.officer",
    "full_name": "Rajendra Mane (Revenue Officer)",
    "role": "REVENUE_OFFICER",
    "department": "Revenue & Forest Department",
    "division": "Pune Division (Haveli Tahsil)"
  },
  "permissions": [
    "APPLICATION_VIEW_ASSIGNED",
    "DOCUMENT_VERIFY",
    "APPLICATION_APPROVE",
    "APPLICATION_REJECT",
    "REQUEST_INFORMATION"
  ]
}
```
#### Error Codes
- `401 Unauthorized`: Invalid identifier or incorrect password
- `403 Forbidden`: Account is suspended or inactive
- `422 Unprocessable Content`: Missing mandatory credentials

---

### GET `/api/v1/auth/me`
#### Description
Returns the authenticated profile, active permissions, and departmental role for the current session.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
Any Authenticated Officer
#### Request
- **Headers:** `Authorization: Bearer <token>`
#### Response
```json
{
  "success": true,
  "data": {
    "id": "USR-REV-001",
    "username": "revenue.officer",
    "email": "officer.pune@revenue.gov.in",
    "mobile": "9820011223",
    "full_name": "Rajendra Mane (Revenue Officer)",
    "role": "REVENUE_OFFICER",
    "department": "Revenue & Forest Department",
    "division": "Pune Division (Haveli Tahsil)",
    "is_active": true,
    "created_at": "2026-08-01T00:00:00Z",
    "last_login": "2026-08-30T17:13:45Z"
  },
  "message": "Officer profile retrieved successfully."
}
```

---

### POST `/api/v1/auth/reauthenticate`
#### Description
Validates officer credentials before executing high-security administrative or manual override operations.
#### Authentication
Required (`Bearer <token>`)
#### Request Body
```json
{
  "password": "Officer@2026"
}
```

---

### POST `/api/v1/auth/refresh`
#### Description
Refreshes the active session token without requiring full credential re-entry.
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/auth/logout`
#### Description
Terminates the session and logs the logout event.
#### Authentication
Required (`Bearer <token>`)

---

## 3. ADMINISTRATION & PERSONNEL MANAGEMENT ENDPOINTS

### GET `/api/v1/admin/users`
#### Description
Lists all registered departmental personnel and their assigned roles. Restricted to Administrators.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`DEPARTMENT_ADMINISTRATOR` (`USER_MANAGE`)
#### Error Codes
- `401 Unauthorized`: Unauthenticated
- `403 Forbidden`: Non-admin role attempted access

---

## 4. APPLICATION INGESTION & OPERATIONAL QUEUE ENDPOINTS

### POST `/api/v1/integrations/applications` (Alias: `/api/v1/revenue/applications/ingest`)
#### Description
Primary cross-department integration contract endpoint for GovMesh and external departmental microservices to submit NEW citizen address mutation applications into the Revenue Department. Enforces service authentication, contract version validation (`request_version: "1.0"`), idempotency duplicate prevention, and atomic multi-entity persistence (Application + Consent + Status History + Audit Trail + Departmental Alert).
#### Authentication
Required (`X-GovMesh-API-Key: <key>` or `X-API-Key: <key>` or `Authorization: Bearer <token>`)
#### Role / Permission
Authorized Integration Peer (`GOVMESH_GATEWAY` or `DEPARTMENT_ADMINISTRATOR`)
#### Request Headers
- `X-GovMesh-API-Key`: Pre-shared integration secret key (configured in environment).
- `Content-Type`: `application/json`
#### Request Body
```json
{
  "application_id": "GM-2026-000201",
  "correlation_id": "CORR-2026-000201",
  "request_version": "1.0",
  "source_department": "GOVMESH",
  "service_type": "ADDRESS_CHANGE",
  "priority": "NORMAL",
  "submitted_at": "2026-09-04T10:00:00Z",
  "citizen": {
    "name": "Pooja Suresh Sharma",
    "identifier": "CIT-MH-200201",
    "contact": {
      "phone": "9819922334",
      "email": "pooja.sharma@example.gov.in"
    }
  },
  "application_data": {
    "existing_address": {
      "house_no": "12/A, Gokuldham",
      "street": "FC Road",
      "village": "Shivajinagar",
      "taluka": "Haveli",
      "district": "Pune",
      "pincode": "411005"
    },
    "new_address": {
      "house_no": "B-304, Green Acres",
      "street": "Baner-Pashan Link Road",
      "village": "Baner",
      "taluka": "Haveli",
      "district": "Pune",
      "pincode": "411045"
    },
    "proof_documents": [
      {
        "document_id": "DOC-GM-200201",
        "document_type": "ELECTRICITY_BILL",
        "document_name": "MSEDCL_Bill_Aug2026.pdf",
        "upload_date": "2026-09-04T09:45:00Z",
        "verification_status": "VALIDATED",
        "file_size": "1.1 MB",
        "document_hash": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"
      }
    ],
    "remarks": "Change of residence following property acquisition."
  },
  "consent": {
    "consent_reference": "CONSENT-2026-000201",
    "purpose": "Update Revenue address record & 7/12 land registry linkage",
    "data_scope": "address.change",
    "recipient": "Revenue & Forest Department",
    "granted": true,
    "issued_at": "2026-09-04T09:40:00Z",
    "expires_at": "2027-09-04T09:40:00Z"
  },
  "integrity": {
    "canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "document_hash": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"
  }
}
```
#### Success Response (201 Created)
```json
{
  "success": true,
  "status": "RECEIVED",
  "application_id": "GM-2026-000201",
  "correlation_id": "CORR-2026-000201",
  "message": "Application successfully received by Revenue Department",
  "received_at": "2026-09-04T10:00:00Z"
}
```
#### Idempotent Duplicate Response (200 OK)
```json
{
  "success": true,
  "status": "ALREADY_RECEIVED",
  "application_id": "GM-2026-000201",
  "correlation_id": "CORR-2026-000201",
  "message": "Application was already received",
  "received_at": "2026-09-04T10:00:00Z"
}
```
#### Error Codes
- `400 Bad Request`: `UNSUPPORTED_CONTRACT_VERSION` (unsupported request_version)
- `401 Unauthorized`: `AUTHENTICATION_REQUIRED` (missing or invalid integration API key)
- `409 Conflict`: `APPLICATION_ID_CONFLICT` (application ID exists with conflicting identity)
- `422 Unprocessable Content`: `VALIDATION_ERROR` (missing mandatory fields or invalid PIN code)
- `500 Internal Server Error`: `PERSISTENCE_ERROR` (database atomic commit failure)

---

### GET `/api/v1/revenue/dashboard/summary`
#### Description
Returns aggregated counters for the scrutiny desk: total incoming, pending, processing, verified, rejected, action-required cases, and system connectivity metrics.
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/applications`

#### Description
Retrieves a paginated list of applications with comprehensive search, multi-field filtering, and sorting.
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/applications/completed`
#### Description
Dedicated operational queue listing only finalized applications marked `VERIFIED`.
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/applications/rejected`
#### Description
Dedicated operational queue listing rejected applications along with statutory rejection grounds.
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/applications/action-required`
#### Description
Dedicated operational queue listing cases awaiting citizen clarification (`ACTION_REQUIRED`).
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/applications/{application_id}`
#### Description
Retrieves full application details including legal consent reference, correlation ID, internal address structure, attached proof documents, and complete workflow history.
#### Authentication
Required (`Bearer <token>`)

---

## 5. REVENUE ADDRESS VERIFICATION WORKFLOW ENDPOINTS

### POST `/api/v1/revenue/address/verify`
#### Description
Executes a comprehensive address verification probe across Consent, Address Data, and Document Proof.
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/application/{application_id}/start-review`
#### Description
Transitions an application from `PENDING` to `PROCESSING`, assigning the reviewing officer.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`APPLICATION_VIEW_ASSIGNED`

---

### POST `/api/v1/revenue/application/{application_id}/validate-consent`
#### Description
Evaluates DPDP citizen consent against 8 statutory rules (existence, validity, purpose match, data scope, recipient, expiry, revocation, and applicant match).
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/application/{application_id}/validate-data`
#### Description
Authoritatively validates address completeness (house number, street, village/ward, taluka, district, 6-digit Maharashtra PIN code, and duplicate application detection).
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/application/{application_id}/verify-document`
#### Description
Executes simulated OCR address extraction and 6-part string comparison against the citizen's declared address.
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/application/{application_id}/approve`
#### Description
Authoritative officer finalization approving the address update and setting state to `VERIFIED`. Requires all preconditions: Consent = VALID, Data = VALID, and Document = MATCH / VALIDATED.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`APPLICATION_APPROVE` (`REVENUE_OFFICER`, `SENIOR_REVENUE_OFFICER`)

---

### POST `/api/v1/revenue/application/{application_id}/reject`
#### Description
Rejects the application with a mandatory statutory justification reason and marks state `REJECTED`.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`APPLICATION_REJECT`

---

### POST `/api/v1/revenue/application/{application_id}/request-info`
#### Description
Sets application status to `ACTION_REQUIRED`, specifying required citizen clarifications.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`REQUEST_INFORMATION`

---

### POST `/api/v1/revenue/application/{application_id}/reprocess`
#### Description
Transitions an `ACTION_REQUIRED` application back to `PROCESSING` after citizen response.
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/application/{application_id}/retry`
#### Description
Controlled operational retry for applications in temporary failed or queued states.
#### Authentication
Required (`Bearer <token>`)

---

## 6. PROOF DOCUMENTS & OCR VERIFICATION ENDPOINTS

### POST `/api/v1/revenue/application/{application_id}/documents`
#### Description
Uploads and attaches a proof document (PDF, JPG, PNG, max 10MB) to an open application.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`DOCUMENT_VERIFY`

---

### GET `/api/v1/revenue/application/{application_id}/documents`
#### Description
Lists all proof documents attached to the specified application with current OCR verification results.
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/document/{document_id}`
#### Description
Retrieves metadata and verification status for an individual document.
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/document/{document_id}/preview`
#### Description
Returns a safe, read-only SVG binary representation of the simulated utility bill.
#### Authentication
Required (`Bearer <token>`)
#### Response
- `Content-Type: image/svg+xml`

---

### POST `/api/v1/revenue/document/{document_id}/verify`
#### Description
Triggers an OCR match verification run against the document's extracted particulars.
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/document/{document_id}/override`
#### Description
Authoritative manual override by a Revenue Officer with mandatory reason logging.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`DOCUMENT_VERIFY` / `EXCEPTION_OVERRIDE`

---

## 7. DEPARTMENTAL NOTIFICATIONS ENDPOINTS

### GET `/api/v1/revenue/notifications`
#### Description
Lists role-filtered operational notifications with unread counts and severity levels.
#### Authentication
Required (`Bearer <token>`)

---

### GET `/api/v1/revenue/notifications/unread-count`
#### Description
Returns count of unread notifications for the active officer.
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/notifications/{notification_id}/read`
#### Description
Marks a single notification as read.
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/notifications/mark-all-read`
#### Description
Marks all notifications for the active officer as read.
#### Authentication
Required (`Bearer <token>`)

---

## 8. AUDIT TRAIL & SIMULATION CONTROL ENDPOINTS

### GET `/api/v1/revenue/audit-logs`
#### Description
Retrieves paginated immutable audit logs with officer IDs, actions, and correlation IDs.
#### Authentication
Required (`Bearer <token>`)
#### Role / Permission
`AUDIT_VIEW` (`READ_ONLY_AUDITOR`, `DEPARTMENT_ADMINISTRATOR`, `REVENUE_OFFICER`)

---

### GET `/api/v1/revenue/simulation/failure-mode`
#### Description
Retrieves current failure simulation mode (`NONE`, `API_UNAVAILABLE`, `TIMEOUT`, `INTERNAL_ERROR`).
#### Authentication
Required (`Bearer <token>`)

---

### POST `/api/v1/revenue/simulation/failure-mode`
#### Description
Sets runtime failure simulation mode for SIH demonstration resilience testing.
#### Authentication
Required (`Bearer <token>`)

---

# PRODUCTION API STATUS

All tests verified against deployed production backend: `https://sih-2026-revenue-dept.onrender.com`

| Method | Endpoint | Production URL | HTTP Status | Status |
|--------|----------|----------------|-------------|--------|
| GET | `/` | `https://sih-2026-revenue-dept.onrender.com/` | 200 | ✓ WORKING |
| GET | `/health` | `https://sih-2026-revenue-dept.onrender.com/health` | 200 | ✓ WORKING |
| GET | `/health/db` | `https://sih-2026-revenue-dept.onrender.com/health/db` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/system-info` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/system-info` | 200 | ✓ WORKING |
| POST | `/api/v1/auth/login` | `https://sih-2026-revenue-dept.onrender.com/api/v1/auth/login` | 200 | ✓ WORKING |
| GET | `/api/v1/auth/me` | `https://sih-2026-revenue-dept.onrender.com/api/v1/auth/me` | 200 (401 unauth) | ✓ WORKING |
| POST | `/api/v1/auth/reauthenticate` | `https://sih-2026-revenue-dept.onrender.com/api/v1/auth/reauthenticate` | 200 | ✓ WORKING |
| POST | `/api/v1/auth/refresh` | `https://sih-2026-revenue-dept.onrender.com/api/v1/auth/refresh` | 200 | ✓ WORKING |
| POST | `/api/v1/auth/logout` | `https://sih-2026-revenue-dept.onrender.com/api/v1/auth/logout` | 200 | ✓ WORKING |
| GET | `/api/v1/admin/users` | `https://sih-2026-revenue-dept.onrender.com/api/v1/admin/users` | 200 (403 non-admin) | ✓ WORKING |
| GET | `/api/v1/revenue/dashboard/summary` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/dashboard/summary` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/applications` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/applications` | 200 (401 unauth) | ✓ WORKING |
| GET | `/api/v1/revenue/applications/completed` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/applications/completed` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/applications/rejected` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/applications/rejected` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/applications/action-required` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/applications/action-required` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/applications/{id}` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/applications/GM-2026-000124` | 200 | ✓ WORKING |
| POST | `/api/v1/integrations/applications` | `https://sih-2026-revenue-dept.onrender.com/api/v1/integrations/applications` | 201 (401 unauth) | ✓ WORKING (Phase 13 Contract) |
| POST | `/api/v1/revenue/applications/ingest` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/applications/ingest` | 201 (401 unauth) | ✓ WORKING (Phase 13 Alias) |
| POST | `/api/v1/revenue/address/verify` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/address/verify` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/start-review` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/start-review` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/validate-consent` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/validate-consent` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/validate-data` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/validate-data` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/verify-document` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/verify-document` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/approve` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/approve` | 200 (422 if invalid) | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/reject` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000125/reject` | 200 (422 if empty) | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/request-info` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/request-info` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/reprocess` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/reprocess` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/retry` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/retry` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/application/{id}/documents` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/documents` | 201 (401 unauth) | ✓ WORKING |
| GET | `/api/v1/revenue/application/{id}/documents` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/application/GM-2026-000124/documents` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/document/{id}` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/document/DOC-REV-9081` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/document/{id}/preview` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/document/DOC-REV-9081/preview` | 200 (SVG) | ✓ WORKING |
| POST | `/api/v1/revenue/document/{id}/verify` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/document/DOC-REV-9081/verify` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/document/{id}/override` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/document/DOC-REV-9081/override` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/notifications` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/notifications` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/notifications/unread-count` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/notifications/unread-count` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/notifications/{id}/read` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/notifications/NOTIF-REV-001/read` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/notifications/mark-all-read` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/notifications/mark-all-read` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/audit-logs` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/audit-logs` | 200 | ✓ WORKING |
| GET | `/api/v1/revenue/simulation/failure-mode` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/simulation/failure-mode` | 200 | ✓ WORKING |
| POST | `/api/v1/revenue/simulation/failure-mode` | `https://sih-2026-revenue-dept.onrender.com/api/v1/revenue/simulation/failure-mode` | 200 | ✓ WORKING |

---

# MISSING / BROKEN REVENUE APIs

### Summary
Every endpoint defined in the Revenue backend source code is fully implemented, correctly mounted across `/api/v1` prefixes, and functional on the deployed production service (`https://sih-2026-revenue-dept.onrender.com`).

### Historical Root Cause of 404 / 405 Errors on Vercel
1. **Frontend Host Routing vs Backend API Host:**  
   The frontend domain `https://sih-2026-revenue-dept.vercel.app` is a static Single Page Application (SPA) deployment on Vercel. In earlier revisions, when requests were sent directly to the relative path `/api/v1/...` on the Vercel domain, Vercel matched the SPA rewrite rule (`/(.*) -> /index.html`), returning `200 OK` with HTML (`<!doctype html>...`) for `GET` requests and `405 Method Not Allowed` for `POST` requests.
2. **Resolution Applied:**  
   In `frontend/src/services/api.ts`, the frontend client explicitly points to the deployed FastAPI backend at `https://sih-2026-revenue-dept.onrender.com` via `PRODUCTION_BACKEND_URL` and `VITE_API_URL` / `VITE_API_BASE_URL`.
3. **No Missing Endpoints:**  
   Zero backend routes are missing. 100% of frontend `apiService` calls match authoritative FastAPI endpoints on Render.
