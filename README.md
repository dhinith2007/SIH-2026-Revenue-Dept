# GovMesh — Revenue & Forest Department (Department 1)

> **SIH 2026 Prototype — Problem Statement SIH26129**  
> **Authoritative Department Module**: Department 1 — Revenue & Forest Department (महसूल व वन विभाग)  
> **Status**: Phases 01–06 Completed & Verified  

---

> [!IMPORTANT]
> **DISCLAIMER & SCOPE NOTICE**:  
> This software is a simulated departmental prototype developed for the Smart India Hackathon (SIH 2026) demonstration. It is **NOT** an official production Maharashtra Government system and does **NOT** connect to production government APIs (e.g. real UIDAI Aadhaar, NSDL PAN, MahaBhulekh live servers). All citizen identities, property documents, utility receipts, and OCR extractions are simulated for demonstration and evaluation purposes.

---

## 1. Overview & Architecture

**GovMesh** is a decentralized data interoperability mesh enabling government departments to coordinate citizen services while preserving departmental autonomy and data sovereignty.

Within this architecture, the **Revenue & Forest Department** operates as an independent backend-authoritative microservice and officer scrutiny portal.

```
                  CITIZEN / GOVMESH CHANNEL
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│       Revenue Department Gateway & Service (FastAPI)        │
│                                                             │
│  [Health & Telemetry]      [JWT & RBAC Security Engine]     │
│   GET /health               POST /api/v1/revenue/auth/login │
│                                                             │
│  [DPDP Consent Engine]     [Address Validation Engine]      │
│   POST .../consent/validate POST .../address/validate       │
│                                                             │
│  [AI/OCR Assistive Engine] [Officer Decision Desk]          │
│   POST .../documents        POST .../application/:id/approve│
│   POST .../document/:id/ocr POST .../application/:id/reject │
│                                                             │
│  [Immutable Audit Ledger]  [Notification Center]            │
│   GET .../audit-logs        GET .../notifications           │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────────┐   ┌───────────────────────────┐
│ Revenue Officer Portal (React)│   │  Departmental Persistence │
│ - Scrutiny Stepper Workspace  │   │  - PostgreSQL Engine      │
│ - Side-by-Side OCR Desk       │   │  - High-Speed In-Memory   │
│ - Sandboxed Document Preview  │   │    Hybrid Fallback        │
│ - Operational Timeline        │   │  - 8 Seed Demo Cases      │
└───────────────────────────────┘   └───────────────────────────┘
```

---

## 2. Technology Stack

- **Backend Service**: Python 3.11, FastAPI 0.110+, Pydantic v2, PyJWT, Bcrypt, Python-Multipart, SQLAlchemy 2.0.
- **Frontend Portal**: React 18, TypeScript 5, Vite 5, Tailwind CSS, Lucide React, Vitest, Testing Library.
- **Persistence**: Hybrid architecture (PostgreSQL 16 support with high-speed in-memory seeded store and fallback).
- **Deployment Packaging**: Multi-stage Dockerfiles, Nginx SPA reverse proxy, Docker Compose.

---

## 3. Local Setup & Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm 9+
- Git

### A. Backend Service Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend will be live at `http://localhost:8000`.  
Interactive API Docs (Swagger): `http://localhost:8000/api/v1/docs`

### B. Frontend Portal Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend Portal will be live at `http://localhost:5173`.

### C. Docker Compose (Full Stack)
```bash
# Start PostgreSQL, Backend, and Nginx Frontend in one command
docker-compose up --build
```
- Frontend Portal: `http://localhost:5173`
- Backend Service: `http://localhost:8000`
- Database: `localhost:5432`

---

## 4. Environment Configuration

Copy `.env.example` to `.env` to customize settings:

```ini
# Environment
APP_ENV=development
DEBUG=true

# Service Ports
BACKEND_PORT=8000
FRONTEND_PORT=5173
DB_PORT=5432

# Frontend Target Backend URL
VITE_API_URL=http://localhost:8000

# Security (Set 32+ char random string in production)
JWT_SECRET=dev-revenue-department-secret-key-sih26129-do-not-use-in-prod-32bytes
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Allowed Frontend Origins
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000

# Optional PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/revenue_db

# Phase 05 Operational Simulation Mode (NONE | API_UNAVAILABLE | TIMEOUT | INTERNAL_ERROR)
FAILURE_MODE=NONE
SIMULATION_LATENCY_MS=0
```

---

## 5. Authentication & Role-Based Access Control (RBAC)

Authentication uses standard JWT Bearer Tokens. The portal includes safe demo accounts for SIH evaluation:

| Role | Username | Password | Key Permissions |
|:---|:---|:---|:---|
| **Revenue Officer** | `revenue.officer` | `Officer@2026` | `DOCUMENT_VERIFY`, `APPLICATION_APPROVE`, `APPLICATION_REJECT`, `REQUEST_INFORMATION` |
| **Senior Revenue Officer** | `senior.officer` | `Senior@2026` | Officer permissions + `ESCALATED_CASE_REVIEW`, `EXCEPTION_OVERRIDE` |
| **Department Administrator** | `revenue.admin` | `Admin@2026` | `USER_MANAGE`, `SERVICE_METADATA_CONFIGURE`, `SYSTEM_HEALTH_VIEW` |
| **Read-only Auditor** | `revenue.auditor` | `Auditor@2026` | `AUDIT_VIEW`, `APPLICATION_VIEW_ALL` (Read-only) |

---

## 6. Complete Revenue API Catalogue

All versioned APIs are mounted under `/api/v1/revenue`.

### Health & Telemetry
| Method | Endpoint | Auth | Description |
|:---|:---|:---|:---|
| `GET` | `/health` | Public | Root service health probe |
| `GET` | `/health/db` | Public | Root database health probe |
| `GET` | `/api/v1/revenue/health` | Public | Versioned service health status |
| `GET` | `/api/v1/revenue/info` | Public | System metadata & phase information |

### Authentication & Session
| Method | Endpoint | Auth | Description |
|:---|:---|:---|:---|
| `POST` | `/api/v1/revenue/auth/login` | Public | Authenticate with username & password; returns JWT token |
| `POST` | `/api/v1/revenue/auth/logout` | Required | Invalidate current session |
| `GET` | `/api/v1/revenue/auth/me` | Required | Retrieve current user profile and permissions |
| `POST` | `/api/v1/revenue/auth/reauthenticate` | Required | Re-auth challenge for sensitive operations |

### Applications & Dashboard
| Method | Endpoint | Auth | Description |
|:---|:---|:---|:---|
| `GET` | `/api/v1/revenue/dashboard/summary` | Required | Metrics: pending, processing, verified, rejected, avg time |
| `GET` | `/api/v1/revenue/applications` | Required | Paginated list with search, status filter, and sorting |
| `GET` | `/api/v1/revenue/application/{id}` | Required | Full application detail, consent record, and history |
| `GET` | `/api/v1/revenue/audit-logs` | Required | Paginated immutable audit ledger |

### Verification & Officer Workflow
| Method | Endpoint | Auth / Permission | Description |
|:---|:---|:---|:---|
| `POST` | `/api/v1/revenue/consent/validate` | `DOCUMENT_VERIFY` | DPDP consent rules 1–8 validation |
| `POST` | `/api/v1/revenue/address/validate` | `DOCUMENT_VERIFY` | 6-part address completeness check |
| `POST` | `/api/v1/revenue/address/verify` | `DOCUMENT_VERIFY` | Comprehensive probe: Consent + Address + Doc |
| `POST` | `/api/v1/revenue/application/{id}/start-review` | `DOCUMENT_VERIFY` | Transitions `PENDING` → `PROCESSING` |
| `POST` | `/api/v1/revenue/application/{id}/approve` | `APPLICATION_APPROVE` | Approves application → `VERIFIED` |
| `POST` | `/api/v1/revenue/application/{id}/reject` | `APPLICATION_REJECT` | Rejects application with mandatory reason → `REJECTED` |
| `POST` | `/api/v1/revenue/application/{id}/request-info` | `REQUEST_INFORMATION` | Dispatches query to citizen → `ACTION_REQUIRED` |
| `POST` | `/api/v1/revenue/application/{id}/reprocess` | `DOCUMENT_VERIFY` | Citizen query response loop → `PROCESSING` |
| `POST` | `/api/v1/revenue/application/{id}/retry` | `DOCUMENT_VERIFY` | Resumes stalled/failed processing |

### Proof Documents & AI/OCR Scrutiny (Phase 06)
| Method | Endpoint | Auth / Permission | Description |
|:---|:---|:---|:---|
| `POST` | `/api/v1/revenue/application/{id}/documents` | `DOCUMENT_VERIFY` | Upload & attach PDF/JPG/PNG proof document |
| `GET` | `/api/v1/revenue/application/{id}/documents` | Required | List attached documents with verification states |
| `GET` | `/api/v1/revenue/document/{id}` | Required | Retrieve document metadata & OCR extraction |
| `GET` | `/api/v1/revenue/document/{id}/preview` | Required | Safe read-only SVG/image preview stream |
| `POST` | `/api/v1/revenue/document/{id}/verify` | `DOCUMENT_VERIFY` | Executes OCR extraction & 6-part matching |
| `POST` | `/api/v1/revenue/document/{id}/override` | `DOCUMENT_VERIFY` | Officer manual override with mandatory reason |

### Operational Visibility & Notifications
| Method | Endpoint | Auth | Description |
|:---|:---|:---|:---|
| `GET` | `/api/v1/revenue/notifications` | Required | Retrieve departmental alerts & dispatches |
| `POST` | `/api/v1/revenue/notifications/{id}/read` | Required | Mark alert as read |
| `GET` | `/api/v1/revenue/simulation/failure-mode` | Required | Inspect current failure simulation state |
| `POST` | `/api/v1/revenue/simulation/failure-mode` | `USER_MANAGE` | Inject operational fault (NONE, TIMEOUT, etc.) |

---

## 7. Integration Contract for Team Members

When another service or team member integrates with the Revenue Department, follow this standard contract:

### A. Standard Headers
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
X-Correlation-ID: CORR-2026-000124
Content-Type: application/json
```

### B. Standard Response Envelope
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully."
}
```

### C. Standard Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "DOCUMENT_MISMATCH",
    "message": "Discrepancy detected in supporting document: Taluka (Document: 'Baramati', Requested: 'Maval').",
    "correlationId": "CORR-2026-000129",
    "details": null
  }
}
```

### D. Step-by-Step Integration Flow
1. **Authenticate**:
   `POST /api/v1/revenue/auth/login` with `{"username": "revenue.officer", "password": "Officer@2026"}`.
2. **Fetch Application**:
   `GET /api/v1/revenue/application/GM-2026-000124`.
3. **Execute Comprehensive Verification**:
   `POST /api/v1/revenue/address/verify` with `{"application_id": "GM-2026-000124"}`.
4. **Inspect Document & OCR Result**:
   `POST /api/v1/revenue/document/DOC-REV-9081/verify`.
5. **Make Officer Decision**:
   `POST /api/v1/revenue/application/GM-2026-000124/approve` with `{"notes": "Verified against municipal electricity bill."}`.
6. **Confirm Audit Ledger**:
   `GET /api/v1/revenue/audit-logs?application_id=GM-2026-000124`.

---

## 8. Demonstration Test Scenarios

| Scenario | Application ID | Key Characteristic | Expected Outcome |
|:---|:---|:---|:---|
| **Demo 1 (Happy Path)** | `GM-2026-000124` | Valid DPDP consent, complete 6-part address, matching electricity bill | 100% Assistive Match Score → Ready for Officer Approval (`VERIFIED`). |
| **Demo 2 (Expired Consent)** | `GM-2026-000127` | Citizen DPDP consent expired in past | Blocked by Consent Engine (`CONSENT_EXPIRED`, 422). |
| **Demo 3 (Missing Document)** | `GM-2026-000128` | Application submitted with empty document list | Officer dispatches `[Request Information]` → `ACTION_REQUIRED`. |
| **Demo 4 (Address Mismatch)** | `GM-2026-000129` | Document has Baramati taluka; requested address is Maval | AI/OCR flags `MISMATCH` with natural language explanation → `[Reject]`. |
| **Demo 5 (Incomplete Address)** | `GM-2026-000130` | Missing village and taluka in request payload | Data Validation Engine flags missing geographical keys. |
| **Demo 6 (Finalized Immutable)** | `GM-2026-000131` | Status `VERIFIED` | State is immutable; modifications rejected with `409 Conflict`. |

---

## 9. Automated Regression Testing

### Backend Test Suite
```bash
cd backend
python -m pytest
```
- **93 / 93 Tests Passed (100%)** across 8 test suites (`test_api.py`, `test_applications.py`, `test_auth.py`, `test_health.py`, `test_phase05_operations.py`, `test_phase06_documents.py`, `test_rbac.py`, `test_workflow.py`).

### Frontend Vitest Suite
```bash
cd frontend
npm test -- --run
```
- **18 / 18 Tests Passed (100%)** across 6 test suites (`App.test.tsx`, `Applications.test.tsx`, `Auth.test.tsx`, `Documents.test.tsx`, `Operations.test.tsx`, `Workflow.test.tsx`).

### Frontend Production Build
```bash
cd frontend
npm run build
```
- Clean bundle generation with zero TypeScript strictness errors.

---

## 10. Deployment Readiness & Containerization

### Standalone Production Commands
- **Backend**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- **Frontend**:
  ```bash
  npm run build
  # Serve dist/ with Nginx, Caddy, or static host
  ```

### Docker Container Deployment
- **Backend Image**: `docker build -t revenue-backend ./backend`
- **Frontend Image**: `docker build -t revenue-frontend ./frontend`
- **Compose Stack**: `docker-compose up -d`

---

## 11. Known Limitations & Prototype Boundaries

1. **Simulated AI/OCR Engine**: Operates deterministically for SIH demonstration without external paid OCR cloud dependencies.
2. **Ephemeral Document Storage**: Document binaries and SVG previews are rendered safely in-memory / streamed without leaking server filesystem paths.
3. **Database Fallback**: Runs with PostgreSQL or instant in-memory fallback without requiring manual DB migrations.
4. **Scope Boundary**: Strictly restricted to Revenue & Forest Department land records and residence address verification workflows.
HIII Dhinith 
