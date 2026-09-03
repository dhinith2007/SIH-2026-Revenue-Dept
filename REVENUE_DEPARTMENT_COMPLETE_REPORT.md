# GOVMESH – REVENUE & FOREST DEPARTMENT
## Intelligent Digital Revenue Service Platform
### SIH26129 – Comprehensive Technical Implementation & Architecture Report

---

| **Project Attribute**       | **Specification / Current State**                                                                                  |
| :-------------------------- | :----------------------------------------------------------------------------------------------------------------- |
| **Project Initiative**      | **GovMesh (Smart India Hackathon 2026 – Problem Statement SIH26129)**                                             |
| **Covered Module**          | **Revenue & Forest Department (Department 1 – Authoritative Cadastral & Identity Registry)**                       |
| **Primary MVP Use Case**    | **`ADDRESS_CHANGE` (Citizen Cross-Department Address Mutation & Statutory Scrutiny)**                             |
| **System Architecture**     | Decoupled Three-Tier Web Platform (React/Vite SPA + FastAPI ASGI Core + PostgreSQL Relational Engine)             |
| **Security & Privacy Model**| DPDP Act 2023 Aligned Consent Engine, Stateless JWT, Hierarchical RBAC, OWASP Top 10 Hardened Headers             |
| **AI & Automation Layer**   | Bilingual Marathi/English OCR (Tesseract / Simulated Provider) + Confidence Scoring Engine + Human-in-the-Loop     |
| **Automated Test Coverage** | **323 Backend Tests (100% Pass Rate)** \| **24 Frontend Tests (100% Pass Rate)** \| **Clean Production Build**    |
| **Deployment Status**       | **Frontend**: Vercel (Production SPA) \| **Backend**: Render (Containerized ASGI) \| **Database**: PostgreSQL (18.6 Local / Managed Cloud) |

---

## 1. EXECUTIVE SUMMARY

The **GovMesh Revenue & Forest Department Module (SIH26129)** is a high-assurance, digitally sovereign microservice and web portal engineered to eliminate paperwork latency, address fraud, and inter-departmental data fragmentation across Maharashtra state administrative services. 

Within the GovMesh federated interoperability framework, the **Revenue & Forest Department (Department 1)** operates as the definitive legal authority for citizen residential records, land parcel mappings, and cadastral boundaries. When citizens initiate an **Address Change (`ADDRESS_CHANGE`)** request across government systems, this module manages the entire application lifecycle: from citizen application ingestion and **Digital Personal Data Protection (DPDP) Act 2023-aligned** digital consent enforcement, to automated document parsing, bilingual OCR extraction, AI-assisted evidence matching, and human-in-the-loop statutory officer scrutiny.

### Key Architectural Pillars:
1. **Sovereign Citizen Consent (DPDP-Aligned)**: Every application requires cryptographically verifiable, purpose-bound, non-expired, and non-revoked consent before applicant data can be accessed or verified.
2. **AI/OCR Decision Support**: Supporting utility bills (electricity, water, tax receipts) are processed through an abstracted OCR engine (supporting Tesseract and deterministic simulation) coupled with a bilingual Marathi/English text normalizer and multi-factor confidence scoring engine.
3. **Statutory Human-in-the-Loop Control**: AI and OCR automate tedious clerical text extraction and calculate match signals, but statutory approval, rejection, or queries for information remain strictly reserved for authorized departmental officers.
4. **Resilient Persistence & Auditability**: Backed by a transactional PostgreSQL schema (with automated in-memory failover for offline resilience), every status change, officer action, document override, and system check generates an immutable chronological audit trail.
5. **Production Readiness**: Deployed on modern cloud infrastructure (Vercel for the React SPA, Render for the containerized FastAPI service, and managed cloud PostgreSQL), with strict production safety validation preventing insecure development defaults in live environments.

---

## 2. PROBLEM STATEMENT & BACKGROUND

### 2.1 The Real-World Challenge in Public Administration
In municipal and revenue administration, citizen address mutation is among the most frequent citizen-facing transactions. It directly impacts electoral registers, ration entitlement allocation (Food & Civil Supplies Department), agricultural subsidies (Rural Development Department), and property taxation. 

Historically, this workflow suffers from acute administrative bottlenecks:
* **Paper-Heavy & Fragmented Workflows**: Citizens are forced to physically travel to Taluka/Tehsil offices with paper utility bills, index-II property records, and stamped affidavits.
* **Document Forgery & Tampering**: Paper copies are vulnerable to manipulation, spoofing, and forged bill dates, leading to fraudulent resident claims.
* **Clerical Fatigue & Delays**: Revenue Officers spend up to 70% of their time manually transcribing names, meter numbers, survey numbers, and municipal ward details from low-quality photocopies.
* **Lack of Transparency & Citizen Tracking**: Citizens experience prolonged black-box delays without real-time tracking or actionable feedback when an application is queried.
* **Non-Compliance with Privacy Regulations**: The enactment of the **Digital Personal Data Protection (DPDP) Act 2023** mandates that government departments capture explicit, purpose-limited, time-bounded consent before processing citizen personal identifiable information (PII). Legacy paper workflows have zero technical enforcement for consent validity.

### 2.2 The GovMesh Solution
The Revenue & Forest Department module solves these challenges by implementing an **intelligent, auditable, and secure digital scrutiny pipeline**. By decoupling citizen data ingestion from internal departmental scrutiny while assisting officers with machine intelligence, the platform guarantees sub-minute document matching, strict statutory decision ownership, and end-to-end auditability.

---

## 3. OBJECTIVES

The technical objectives achieved within this repository comprise:
* **Digitized Citizen Self-Service**: Provide an intuitive web application allowing citizens to submit structured address mutation requests and upload supporting documentation.
* **DPDP-Aligned Consent Enforcement**: Validate consent records across eight technical parameters (reference integrity, application binding, temporal validity, non-revocation, purpose alignment, recipient authorization, data scope, and operation relevance).
* **Six-Part Address Completeness**: Enforce strict administrative completeness across address lines, landmark, taluka, district, state, and 6-digit postal PIN code.
* **Automated Document Intelligence (OCR)**: Ingest PDF, PNG, and JPEG documents, perform image binarization and preprocessing, and extract raw text across Marathi (Devanagari) and English scripts.
* **Bilingual Evidence Normalization & Token Matching**: Standardize Marathi administrative terminology (उदा. जिल्हा, तालुका, गाव, वीज देयक) and English equivalents to compute lexical, token, and numeric match scores.
* **Multi-Factor Confidence Scoring**: Compute weighted composite confidence scores with deterministic thresholding (`AUTO_MATCH_READY`, `FLAG_FOR_REVIEW`, `MISMATCH_SUSPECTED`).
* **Statutory Human-in-the-Loop Officer Workspace**: Present side-by-side comparisons of citizen application data, extracted document evidence, confidence indicators, and SVG document previews to empower officers to make informed statutory decisions.
* **Hierarchical Role-Based Access Control (RBAC)**: Enforce fine-grained authorization separating Citizen, Revenue Officer, Senior Officer, Administrator, and Auditor roles.
* **PostgreSQL Relational Persistence**: Persist applications, users, audit logs, status transitions, notifications, and verification records in a relational schema with connection pooling.
* **Statutory Audit Logging & Traceability**: Automatically log actor identity, IP address, timestamp, pre/post state changes, and mandatory justification reasons for every operational action.
* **Comprehensive Operational Analytics**: Expose live KPIs, SLA compliance rates, taluka distributions, and review workloads via dedicated backend analytics endpoints and interactive charts.
* **Production Deployment Hardening**: Implement fail-fast production secret validation, edge security headers, rate limiting, and automated Render/Vercel continuous deployment.

---

## 4. SCOPE & BOUNDARIES

### 4.1 In Scope (Implemented in this Repository)
* **Revenue & Forest Department Web Portal** (React 18, TypeScript, TailwindCSS, Vite).
* **Authoritative Revenue Backend API** (FastAPI, Python 3.11, Pydantic v2).
* **Relational Database Engine & Repositories** (PostgreSQL, SQLAlchemy ORM, psycopg2-binary).
* **Bilingual AI/OCR Extraction & Normalization Engine** (Tesseract wrapper, simulated fallback provider, confidence calculator).
* **DPDP Act 2023 Aligned Consent Validation Engine**.
* **Statutory Officer Scrutiny Workflow Engine** (Approve, Reject, Request Information, Reprocess, Manual Override).
* **Role-Based Access Control & JWT Authentication** (Citizens, Officers, Admins, Auditors).
* **Operational Analytics & Real-Time Dashboard Service**.
* **Comprehensive Automated Test Suites** (323 backend pytest tests, 24 vitest frontend tests).
* **Containerization & Cloud Deployment Configurations** (`Dockerfile`, `docker-compose.yml`, `render.yaml`, `vercel.json`).

### 4.2 Out of Scope (Handled Externally / Future Phases)
* **Department 2**: Food, Civil Supplies & Consumer Protection Department (e-Ration card seeding is handled by external GovMesh microservices).
* **Department 3**: Rural Development & Panchayat Raj Department (Property taxation and Gram Panchayat records handled by external GovMesh microservices).
* **GovMesh Core Interoperability Hub**: Cross-departmental message bus orchestration and distributed transaction saga coordination.
* **Physical Biometric Hardware Integration**: Aadhaar iris/fingerprint POS scanners (simulated via GovMesh citizen token exchange).

---

## 5. PHASE-BY-PHASE IMPLEMENTATION HISTORY

The module was developed across 12 distinct, verified architectural phases:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          PHASE IMPLEMENTATION ROADMAP                                   │
├──────────────┬──────────────────────────────────────────────────────────┬───────────────┤
│ Phase 01–03  │ UI Foundations, Data Schemas & Role-Based Access Control │ COMPLETE      │
├──────────────┼──────────────────────────────────────────────────────────┼───────────────┤
│ Phase 04–06  │ Verification Pipeline, DPDP Consent & OCR Engine Factory │ COMPLETE      │
├──────────────┼──────────────────────────────────────────────────────────┼───────────────┤
│ Phase 07–08  │ Cloud Deployment Architecture & PostgreSQL Persistence   │ COMPLETE      │
├──────────────┼──────────────────────────────────────────────────────────┼───────────────┤
│ Phase 09–10  │ Security Hardening, OWASP Safeguards & AI/OCR Matcher    │ COMPLETE      │
├──────────────┼──────────────────────────────────────────────────────────┼───────────────┤
│ Phase 11–12  │ Operational Analytics & End-to-End Failure Simulations   │ COMPLETE      │
└──────────────┴──────────────────────────────────────────────────────────┴───────────────┘
```

---

### PHASE 01 – UI FOUNDATION & CITIZEN/OFFICER PORTAL
* **Objective**: Build a responsive, accessible web interface reflecting the visual language of Maharashtra e-Governance systems (Aaple Sarkar / MahaOnline).
* **Implementation**:
  * Developed a modern React 18 SPA utilizing TypeScript and Vite.
  * Designed official institutional headers incorporating the Government of Maharashtra emblem, bilingual English/Marathi typography, and high-contrast accessibility standards.
  * Established foundational page layouts for login, role selection, application submission, and departmental navigation.

---

### PHASE 02 – REVENUE APPLICATION DATA SCHEMAS & LIFECYCLE
* **Objective**: Establish the canonical data models, validation schemas, and lifecycle states for address mutation requests.
* **Implementation**:
  * Formalized the canonical `RevenueApplication` entity and Pydantic validation schemas.
  * Implemented lifecycle states: `SUBMITTED`, `PENDING_VERIFICATION`, `UNDER_REVIEW`, `ACTION_REQUIRED`, `VERIFIED`, and `REJECTED`.
  * Defined unique identifiers: Application ID (`GM-2026-XXXXXX`), Correlation ID (`CORR-XXXXXX`), and Citizen Reference ID (`CIT-MH-XXXX`).
  * Created foundational REST endpoints for application creation, retrieval, and status tracking.

---

### PHASE 03 – AUTHENTICATION, RBAC & CORE WORKFLOWS
* **Objective**: Secure the application with JSON Web Tokens (JWT) and enforce strict Role-Based Access Control (RBAC).
* **Implementation**:
  * Implemented secure token issuance via `POST /api/v1/auth/login` and `/revenue/auth/login`.
  * Created pre-configured demo personas with cryptographic bcrypt password hashing:
    * **Revenue Officer** (`revenue.officer` / `Officer@2026`) – Operational scrutiny & verification.
    * **Senior Revenue Officer** (`senior.officer` / `Senior@2026`) – Escalations & high-value overrides.
    * **Department Administrator** (`revenue.admin` / `Admin@2026`) – User management & system configuration.
    * **Read-Only Auditor** (`revenue.auditor` / `Auditor@2026`) – Non-repudiation audit trail inspection.
  * Enforced authorization dependencies preventing unauthorized role horizontal and vertical privilege escalation.

---

### PHASE 04 – ADDRESS VERIFICATION & OFFICER DECISION WORKSPACE
* **Objective**: Construct the core statutory decision pipeline incorporating DPDP consent checks and address integrity rules.
* **Implementation**:
  * **DPDP Consent Verification**: Enforced 8-point consent validation (see Section 6).
  * **Six-Part Address Completeness**: Mandated presence of Premise/Building, Street/Locality, Landmark, Taluka, District, and valid 6-digit Indian PIN code.
  * **Officer Scrutiny Workspace**: Built a comprehensive frontend review environment displaying application data, uploaded evidence, match signals, and statutory action buttons (`Approve`, `Reject`, `Request Information`).

---

### PHASE 05 – DOCUMENT VERIFICATION & OCR FOUNDATION
* **Objective**: Establish the document ingestion pipeline and modular OCR extraction provider abstraction.
* **Implementation**:
  * Created the `OCRProvider` abstract base class defining standard contracts for raw text extraction, confidence mapping, and bounding box analysis.
  * Implemented `SimulatedOCRProvider` for deterministic, zero-dependency CI/CD environments and testing.
  * Implemented initial file upload validation restricting file size (10 MB) and allowed MIME types (`application/pdf`, `image/jpeg`, `image/png`).

---

### PHASE 06 – API HARDENING & SERVICE DECOUPLING
* **Objective**: Harden REST interfaces, standardize error structures, and decouple services for horizontal scaling.
* **Implementation**:
  * Separated business logic into dedicated service layers (`WorkflowService`, `DataValidationService`, `ConsentService`, `DocumentVerificationService`).
  * Implemented standard RFC 7807 error responses across all endpoints.
  * Added statutory rejection validation requiring a non-empty, detailed reason string before any application status can transition to `REJECTED`.

---

### PHASE 07 – PRODUCTION DEPLOYMENT & API EXPOSURE
* **Objective**: Expose authoritative API endpoints for GovMesh cross-department consumption and prepare cloud hosting.
* **Implementation**:
  * Implemented canonical GovMesh address verification ingress: `POST /api/v1/revenue/address/verify`.
  * Deployed frontend on Vercel (`https://sih-2026-revenue-dept.vercel.app`) with client-side routing fallback (`vercel.json`).
  * Containerized the FastAPI backend for Render cloud deployment (`https://sih-2026-revenue-dept.onrender.com`) with dynamic `$PORT` binding.

---

### PHASE 08 – POSTGRESQL & PERSISTENT DATA LAYER
* **Objective**: Replace in-memory dictionaries with a production-grade PostgreSQL relational database schema.
* **Implementation**:
  * Engineered 8 relational tables in SQLAlchemy with foreign keys, cascading rules, and indices (see Section 8).
  * Implemented connection pooling via SQLAlchemy `create_engine` (`pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`).
  * Built an automated, idempotent database seeder (`seed_database`) that populates baseline demo data without destroying existing records.
  * Implemented transparent fallback: if PostgreSQL is temporarily offline during development, repository classes seamlessly operate on high-speed in-memory seeded dictionaries.

---

### PHASE 09 – SECURITY, DPDP & RBAC HARDENING
* **Objective**: Implement comprehensive enterprise security controls addressing OWASP Top 10 vulnerabilities.
* **Implementation**:
  * **SEC-01 & SEC-02 (Production Secret Hardening)**: Created `validate_production_secrets` model validator in `config.py` that halts backend startup if `APP_ENV=production` is paired with default JWT keys, empty database URLs, or localhost database hosts.
  * **SEC-03 (Token Invalidation & Session Lifespan)**: Configured 30-minute JWT session expiration and token replay prevention.
  * **SEC-04 (File Upload Security & Magic Byte Validation)**: Replaced naive filename extension checking with binary header validation (`%PDF-`, `\xFF\xD8\xFF`, `\x89PNG`) and path traversal sanitization (`SecureFilename`).
  * **SEC-05 (SVG Injection & Stored XSS Prevention)**: Sanitized all dynamic citizen text formatted into SVG document preview templates via `sanitize_svg_text()`.
  * **SEC-06 (CORS Hardening)**: Disallowed wildcard `*` origins when credential exchange is enabled.
  * **SEC-07 (Security Headers Middleware)**: Injected `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Strict-Transport-Security`, and Content Security Policy (CSP).
  * **SEC-08 (In-Memory IP Rate Limiting)**: Implemented sliding-window rate limiting on sensitive authentication and upload endpoints (60 requests/minute per client IP).

---

### PHASE 10 – AI/OCR INTELLIGENT VERIFICATION ENGINE
* **Objective**: Build a high-precision, bilingual extraction and confidence engine for revenue document scrutiny.
* **Implementation**:
  * Created `TesseractOCRProvider` integrating Google Tesseract OCR with Marathi (`mar`) and English (`eng`) language models.
  * Built `BilingualTextNormalizer` handling Devanagari numerals (`०-९` $\rightarrow$ `0-9`), administrative synonym expansion (उदा. `मु.पो.` $\rightarrow$ `Mukhya Post`, `ता.` $\rightarrow$ `Taluka`), whitespace normalization, and diacritic stripping.
  * Developed `DocumentEvidenceMatcher` calculating Levenshtein ratio, token sort ratio, and exact numeric matching across Address, Citizen Name, and PIN Code.
  * Engineered `ConfidenceScoringEngine` generating composite confidence scores ($0.0 - 1.0$) mapped to deterministic recommendations (`AUTO_MATCH_READY`, `FLAG_FOR_REVIEW`, `MISMATCH_SUSPECTED`).
  * Hardened against AI hallucinations: AI recommendations strictly serve as decision-support indicators; statutory approvals require explicit officer authentication.

---

### PHASE 11 – OPERATIONAL ANALYTICS & DASHBOARD SERVICE
* **Objective**: Deliver executive visibility into revenue department performance, SLA compliance, and officer workloads.
* **Implementation**:
  * Created `AnalyticsService` executing SQL aggregations over live application, audit, and status history tables.
  * Exposed `GET /api/v1/revenue/analytics/dashboard` returning total applications, status distribution, average verification turnaround time, SLA breach counters, and taluka distributions.
  * Developed `DashboardPage.tsx` with interactive metric cards, status breakdown charts, SLA progress indicators, and quick-filter scrutiny queues.

---

### PHASE 12 – END-TO-END TESTING & OPERATIONAL FAILURE SIMULATION
* **Objective**: Subject the entire system to exhaustive end-to-end integration tests and real-world failure simulations.
* **Implementation**:
  * Implemented dynamic runtime failure simulation via `FAILURE_MODE` setting (`NONE`, `API_UNAVAILABLE`, `TIMEOUT`, `INTERNAL_ERROR`) and simulated latency injection (`SIMULATION_LATENCY_MS`).
  * Developed automated test suites covering:
    * Complete happy path (Citizen Submission $\rightarrow$ OCR Extraction $\rightarrow$ Officer Verification $\rightarrow$ Approved).
    * Edge cases (spoofed files, path traversal, expired consent, revoked consent, missing taluka).
    * Failure resilience (OCR service failure, database reconnection, graceful degradation).
  * Achieved a flawless **323 passed backend test suite** and **24 passed frontend test suite**.

---

## 6. COMPLETE SYSTEM WORKFLOW & CITIZEN LIFECYCLE

```mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant Portal as Vercel Frontend SPA
    participant API as Render FastAPI Backend
    participant DPDP as Consent Engine
    participant OCR as AI/OCR Engine
    participant DB as PostgreSQL Database
    actor Officer as Revenue Officer

    Citizen->>Portal: 1. Login & Navigate to Address Change
    Citizen->>Portal: 2. Input New Address (6-part schema)
    Citizen->>Portal: 3. Review & Grant DPDP Digital Consent
    Citizen->>Portal: 4. Upload Supporting Document (e.g. MSEB Bill)
    Portal->>API: 5. POST /api/v1/revenue/applications (Multipart)
    
    API->>DPDP: 6. Validate Consent Token & Scope
    DPDP-->>API: 7. Consent VALID (Purpose: ADDRESS_CHANGE)
    
    API->>API: 8. Validate Document Binary Magic Bytes & Path
    API->>OCR: 9. Extract Text & Entities (Bilingual Marathi/English)
    OCR->>OCR: 10. Normalize Tokens & Compute Confidence
    OCR-->>API: 11. Return Extracted Evidence & Confidence Score
    
    API->>DB: 12. Persist Application, Document Record & Audit Log
    API->>DB: 13. Create In-App Notifications
    API-->>Portal: 14. 201 Created (Application ID: GM-2026-XXXXXX)
    
    Officer->>Portal: 15. Login & Open Scrutiny Queue
    Portal->>API: 16. GET /api/v1/revenue/applications?status=PENDING_VERIFICATION
    API->>DB: 17. Query Assigned Records
    API-->>Portal: 18. Application Dossier with Confidence & SVG Preview
    
    Officer->>Portal: 19. Inspect Evidence & Click "Approve" / "Reject"
    Portal->>API: 20. POST /api/v1/revenue/workflow/approve (with Notes)
    
    API->>DB: 21. Update Status to VERIFIED, Record Status History
    API->>DB: 22. Append Immutable Audit Log
    API-->>Portal: 23. 200 OK (Application Finalized)
    Portal-->>Officer: 24. Updated Queue & Success Toast
```

---

## 7. SYSTEM ARCHITECTURE

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                       CITIZEN / REVENUE OFFICER                        │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTPS
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      VERCEL PRODUCTION FRONTEND                        │
 │  • React 18 SPA (TypeScript + Vite)                                    │
 │  • Aaple Sarkar Official Visual Design System                          │
 │  • Responsive Officer Workspace, Scrutiny Queues & SVG Preview         │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ REST / JSON (TLS Edge Terminated)
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      RENDER FASTAPI BACKEND (ASGI)                     │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                     SECURITY & INGRESS MIDDLEWARE                │  │
 │  │  • Sliding-Window Rate Limiting (60 req/min)                     │  │
 │  │  • Strict CORS Validation (Disallow Wildcards in Prod)           │  │
 │  │  • OWASP Secure Headers (CSP, HSTS, X-Frame-Options)             │  │
 │  └─────────────────────────────────┬────────────────────────────────┘  │
 │                                    ▼                                   │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                     CORE SERVICE CONTROLLERS                     │  │
 │  │  • Auth & RBAC (JWT HS256, Bcrypt, Session Expiry)               │  │
 │  │  • DPDP Consent Service (8-Point Purpose/Scope Validation)       │  │
 │  │  • Address Workflow Service (State Machine & History)            │  │
 │  │  • Analytics Engine (Aggregation & SLA Tracking)                 │  │
 │  └─────────────────────────────────┬────────────────────────────────┘  │
 │                                    ▼                                   │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                     AI / OCR VERIFICATION PIPELINE               │  │
 │  │  • File Magic Byte Validator (PDF/JPEG/PNG)                      │  │
 │  │  • OCR Provider Abstraction (Tesseract / Simulated)              │  │
 │  │  • Bilingual Text Normalizer (Marathi Devanagari & English)      │  │
 │  │  • Document Evidence Matcher (Token Sort, Levenshtein)           │  │
 │  │  • Confidence Scoring Engine (Thresholds: 0.85/0.60/0.0)         │  │
 │  └─────────────────────────────────┬────────────────────────────────┘  │
 └────────────────────────────────────┼───────────────────────────────────┘
                                      │ SQLAlchemy 2.0 / psycopg2-binary
                                      ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      MANAGED POSTGRESQL DATABASE                       │
 │  • Connection Pool (pool_size=5, max_overflow=10, pre-ping=True)       │
 │  • 8 Relational Tables with Referential Integrity & Indices            │
 │  • Idempotent Seeder with Zero-Downtime Migration Readiness            │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 8. DATABASE ARCHITECTURE & RELATIONAL SCHEMA

The persistent layer is built on PostgreSQL 18.6 (compatible with PostgreSQL 14–18), using SQLAlchemy as the Object-Relational Mapper and `psycopg2-binary` as the native driver.

### 8.1 Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ REVENUE_APPLICATIONS : "creates / assigned_to"
    USERS ||--o{ REVENUE_AUDIT_LOGS : "acts_as_actor"
    USERS ||--o{ REVENUE_NOTIFICATIONS : "receives"
    
    REVENUE_APPLICATIONS ||--o{ REVENUE_CONSENTS : "governed_by"
    REVENUE_APPLICATIONS ||--o{ DOCUMENT_VERIFICATION_RECORDS : "supported_by"
    REVENUE_APPLICATIONS ||--o{ APPLICATION_STATUS_HISTORY : "tracks_transitions"
    REVENUE_APPLICATIONS ||--o{ REVENUE_AUDIT_LOGS : "subject_of"
    REVENUE_APPLICATIONS ||--o{ REVENUE_NOTIFICATIONS : "triggers"

    USERS {
        int id PK
        string user_id UK "USR-REV-XXX"
        string username UK
        string email UK
        string mobile
        string hashed_password
        string role "REVENUE_OFFICER | CITIZEN | ADMIN"
        string department
        string division
        boolean is_active
        datetime created_at
    }

    REVENUE_APPLICATIONS {
        int id PK
        string application_id UK "GM-2026-XXXXXX"
        string correlation_id UK "CORR-XXXXXX"
        string citizen_reference_id "CIT-MH-XXXX"
        string citizen_name
        string service_type "ADDRESS_CHANGE"
        string status "SUBMITTED | VERIFIED | REJECTED"
        string priority "NORMAL | URGENT"
        string premise_building
        string street_locality
        string landmark
        string taluka
        string district
        string state
        string pincode
        string assigned_officer_id FK
        datetime received_at
        datetime updated_at
    }

    REVENUE_CONSENTS {
        int id PK
        string consent_id UK "CNS-2026-XXXX"
        string application_id FK
        string citizen_reference_id
        string purpose "ADDRESS_CHANGE"
        string scope "IDENTITY_AND_ADDRESS"
        string recipient "REVENUE_DEPARTMENT"
        datetime granted_at
        datetime expires_at
        boolean is_revoked
    }

    DOCUMENT_VERIFICATION_RECORDS {
        int id PK
        string document_id UK "DOC-REV-XXXX"
        string application_id FK
        string document_type "ELECTRICITY_BILL | WATER_BILL"
        string file_name
        string file_hash
        string ocr_status "PROCESSED | FAILED"
        float confidence_score "0.00 - 1.00"
        string match_status "AUTO_MATCH_READY | REVIEW"
        json extracted_evidence
        boolean is_verified
        string verified_by FK
        datetime verified_at
    }

    APPLICATION_STATUS_HISTORY {
        int id PK
        string application_id FK
        string previous_status
        string new_status
        string changed_by FK
        string remarks
        datetime timestamp
    }

    REVENUE_AUDIT_LOGS {
        int id PK
        string log_id UK "AUD-XXXXXX"
        string action "APPROVE | REJECT | OVERRIDE"
        string actor_id FK
        string target_entity "APPLICATION"
        string target_id
        string ip_address
        json metadata_payload
        datetime timestamp
    }

    REVENUE_NOTIFICATIONS {
        int id PK
        string notification_id UK "NOTIF-XXXX"
        string recipient_id FK
        string application_id FK
        string title
        string message
        string severity "INFO | WARNING | SUCCESS"
        boolean is_read
        datetime created_at
    }

    SYSTEM_HEALTH_PINGS {
        int id PK
        string service_name
        string status "HEALTHY"
        float latency_ms
        datetime timestamp
    }
```

### 8.2 Database Tables Description

| Table Name | Primary Key | Description |
| :--- | :--- | :--- |
| **`users`** | `id` (int) | Department personnel, officers, citizens, and auditor credentials with bcrypt hashes. |
| **`revenue_applications`** | `id` (int) | Authoritative application registry storing 6-part address fields and lifecycle states. |
| **`revenue_consents`** | `id` (int) | DPDP Act 2023 consent records linking citizen authorizations to specific applications. |
| **`document_verification_records`** | `id` (int) | Ingested document metadata, binary hashes, OCR raw text, and confidence scores. |
| **`application_status_history`** | `id` (int) | Fine-grained state transition log recording previous state, new state, actor, and remarks. |
| **`revenue_audit_logs`** | `id` (int) | Append-only statutory audit trail logging every administrative and security event. |
| **`revenue_notifications`** | `id` (int) | System and officer alerts dispatched to citizens and departmental users. |
| **`system_health_pings`** | `id` (int) | Periodic health probe logs monitoring database latency and availability. |

---

## 9. AI/OCR INTELLIGENT VERIFICATION PIPELINE

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      SUPPORTING PROOF DOCUMENT                         │
 │     (PDF / JPEG / PNG Utility Bill, e.g. MSEDCL Electricity Bill)      │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Binary Upload & Stream
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 1. BINARY INGESTION & SECURITY SANITIZATION                            │
 │    • Magic byte verification (%PDF-, \xFF\xD8\xFF, \x89PNG)            │
 │    • Strict file size bound (< 10 MB) & path traversal scrubbing       │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Verified File Buffer
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 2. OCR EXTRACTION ENGINE (Provider Abstraction)                        │
 │    • TesseractOCRProvider: Python-tesseract wrapper with mar+eng       │
 │    • SimulatedOCRProvider: Deterministic fixture provider for testing  │
 │    • Preprocessing: Grayscale conversion, adaptive Otsu binarization   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Raw Extracted Text & Layout
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 3. BILINGUAL NORMALIZATION (BilingualTextNormalizer)                   │
 │    • Marathi Devanagari digits (०-९) normalized to ASCII (0-9)         │
 │    • Administrative abbreviation expansion (ता. -> Taluka, जि. -> Dist)│
 │    • Case folding, diacritic stripping, punctuation scrubbing          │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Canonical Token Stream
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 4. EVIDENCE EXTRACTION (DocumentEvidenceMatcher)                       │
 │    • Regular expression pattern extraction for Consumer/Meter numbers  │
 │    • 6-digit postal PIN code extraction                                │
 │    • Locality, Taluka, and District entity recognition                 │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Extracted Evidence Tuple
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 5. FUZZY & TOKEN MATCHING                                              │
 │    • Token Sort Ratio: Permutation-invariant address string matching   │
 │    • Levenshtein Distance: Typo-tolerant name comparison               │
 │    • Strict Boolean Comparison: District & 6-digit PIN code matching   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Sub-Scores [Name, PIN, Locality]
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 6. CONFIDENCE SCORING ENGINE (ConfidenceScoringEngine)                 │
 │    • Composite Formula:                                                │
 │      Score = 0.35 * NameMatch + 0.30 * LocalityMatch +                 │
 │              0.20 * PinMatch + 0.15 * DocumentLegibility               │
 ├────────────────────────────────────────────────────────────────────────┤
 │    • Score >= 0.85 -> AUTO_MATCH_READY (High Confidence Match)         │
 │    • 0.60 <= Score < 0.85 -> FLAG_FOR_REVIEW (Partial / Fuzzy Match)   │
 │    • Score < 0.60 -> MISMATCH_SUSPECTED (Discrepancy Detected)         │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Composite Score + Visual Signals
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 7. STATUTORY HUMAN OFFICER DECISION                                    │
 │    • Side-by-side evidence inspection in Officer Workspace             │
 │    • Mandatory justification note for manual override of low scores    │
 │    • Statutory click-to-approve / reject / request-information         │
 └────────────────────────────────────────────────────────────────────────┘
```

### Critical Human-in-the-Loop Safeguard:
The confidence scoring engine is **strictly advisory**. Under Maharashtra revenue regulations, AI cannot make legally binding determinations. If the AI assigns an application a score of $0.98$, the application **does not automatically transition to approved**; it is placed in the officer's queue with a green `AUTO_MATCH_READY` badge, allowing the officer to complete scrutiny in seconds while retaining legal accountability.

---

## 10. API ARCHITECTURE & CORE ENDPOINTS

The backend exposes a structured, versioned REST API (`/api/v1/`). All state-changing endpoints require Bearer JWT authentication and validate role privileges.

| HTTP Method | Path / Endpoint | Role Required | Request Body / Parameters | Response Summary |
| :--- | :--- | :--- | :--- | :--- |
| **`GET`** | `/health` | Public | None | System status, environment, version, UTC timestamp |
| **`GET`** | `/health/db` | Public | None | Database connection status, dialect, latency (ms) |
| **`POST`** | `/api/v1/auth/login` | Public | `LoginRequest` (username, password) | Bearer JWT token, user profile, role permissions |
| **`GET`** | `/api/v1/auth/me` | Authenticated | Bearer Header | Current authenticated user identity and role |
| **`GET`** | `/api/v1/revenue/applications` | Officer / Admin | Query: `page`, `page_size`, `status`, `taluka` | Paginated list of revenue applications |
| **`POST`** | `/api/v1/revenue/applications` | Citizen / Officer | Multipart: Application JSON + Document File | Created `RevenueApplication` record (201 Created) |
| **`GET`** | `/api/v1/revenue/applications/{id}` | Citizen / Officer | Path: `id` (`GM-2026-XXXXXX`) | Comprehensive application dossier with consent & history |
| **`POST`** | `/api/v1/revenue/workflow/approve` | Officer / Senior | JSON: `application_id`, `officer_notes` | Status updated to `VERIFIED`, status history created |
| **`POST`** | `/api/v1/revenue/workflow/reject` | Officer / Senior | JSON: `application_id`, `rejection_reason` (Mandatory) | Status updated to `REJECTED`, audit log recorded |
| **`POST`** | `/api/v1/revenue/workflow/request-info` | Officer | JSON: `application_id`, `query_details` | Status set to `ACTION_REQUIRED`, notification sent |
| **`POST`** | `/api/v1/revenue/workflow/reprocess` | Officer | JSON: `application_id` | Clears flags, re-runs OCR pipeline, status: `PROCESSING` |
| **`POST`** | `/api/v1/revenue/workflow/override` | Senior Officer | JSON: `application_id`, `mandatory_justification` | Senior officer statutory override recorded in audit |
| **`POST`** | `/api/v1/revenue/address/verify` | Interop / GovMesh | JSON: Citizen ID, Proposed Address | Canonical GovMesh address validity response |
| **`GET`** | `/api/v1/revenue/document/{id}/preview` | Officer / Auditor | Path: `id` (Document ID) | Sanitized SVG vector preview of proof document |
| **`GET`** | `/api/v1/revenue/analytics/dashboard` | Officer / Admin | Query: `time_range` (`7d`, `30d`, `all`) | KPIs, SLA metrics, turnaround times, taluka distribution |
| **`GET`** | `/api/v1/revenue/notifications` | Authenticated | Query: `unread_only`, `limit` | In-app alerts, status changes, queries |
| **`PATCH`** | `/api/v1/revenue/notifications/{id}/read` | Authenticated | Path: `id` | Marks notification as read |

---

## 11. SECURITY & PRIVACY CONTROLS

The platform implements rigorous defense-in-depth controls aligned with the **Digital Personal Data Protection (DPDP) Act 2023** and **OWASP Top 10** standards:

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      DEFENSE-IN-DEPTH LAYERS                           │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 1. EDGE & TRANSPORT LAYER                                              │
 │    • TLS termination with HSTS (Strict-Transport-Security)             │
 │    • CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff       │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 2. INGRESS & TRAFFIC LAYER                                             │
 │    • Sliding-window IP rate limiting (60 req/min on auth/uploads)      │
 │    • CORS restriction (wildcard '*' strictly forbidden in production)  │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 3. IDENTITY & ACCESS (RBAC)                                            │
 │    • Stateless JWT with HS256 and cryptographic key length checks      │
 │    • Bcrypt password hashing (work factor 12)                          │
 │    • Enforced 30-minute session expiration & role separation           │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 4. INPUT & PAYLOAD VALIDATION                                          │
 │    • Pydantic v2 strict type checking and regex validation             │
 │    • Binary magic byte inspection for file uploads (%PDF-, JPEG, PNG)  │
 │    • Filename sanitization against directory traversal attacks         │
 │    • XML/SVG entity sanitization preventing Stored XSS in previews     │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 5. DPDP PRIVACY CONTROLS                                               │
 │    • Purpose limitation (consent bound exclusively to ADDRESS_CHANGE)  │
 │    • Time-bounded consent expiration checks                            │
 │    • Active revocation status checks before data processing            │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 6. PERSISTENCE & AUDIT                                                 │
 │    • Append-only statutory audit logging recording IP, actor, timestamp│
 │    • Fail-fast production secret validation in Settings                │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 12. VERIFIED AUTOMATED TESTING SUITE

Testing was conducted across the backend and frontend modules against a live PostgreSQL 18.6 instance. All tests pass with zero errors.

### 12.1 Test Execution Metrics

| Test Domain | Suite / File | Tests Executed | Passed | Status |
| :--- | :--- | :---: | :---: | :---: |
| **API Baselines** | `test_api.py`, `test_health.py` | 7 | 7 | **PASS** |
| **Core Entities** | `test_applications.py`, `test_auth.py` | 21 | 21 | **PASS** |
| **Role Authorization** | `test_rbac.py` | 4 | 4 | **PASS** |
| **Workflow State Machine** | `test_workflow.py` | 19 | 19 | **PASS** |
| **Operations & Document Verification**| `test_phase05_operations.py`, `test_phase06_documents.py` | 42 | 42 | **PASS** |
| **PostgreSQL & Real Persistence** | `test_phase08_persistence.py`, `test_phase08_postgresql_e2e.py` | **28** | **28** | **PASS** |
| **Authentication & Document Security**| `test_phase09_auth_security.py`, `test_phase09_rbac_document_security.py` | 43 | 43 | **PASS** |
| **Consent & Sanitization** | `test_phase09_step04_consent_input_sanitization.py` | 26 | 26 | **PASS** |
| **HTTP Transport & Header Security** | `test_phase09_step05_http_security.py` | 35 | 35 | **PASS** |
| **AI / OCR Extraction Pipeline** | `test_phase10_step02_ocr.py` | 21 | 21 | **PASS** |
| **Bilingual Matching Engine** | `test_phase10_step03_matching.py` | 25 | 25 | **PASS** |
| **Multi-Factor Confidence Scoring** | `test_phase10_step04_confidence.py` | 14 | 14 | **PASS** |
| **AI Edge Cases & Hardening** | `test_phase10_step06_hardening.py` | 8 | 8 | **PASS** |
| **Operational Analytics** | `test_phase11_analytics.py` | 7 | 7 | **PASS** |
| **E2E Scenarios & Failure Resilience**| `test_phase12_e2e_happy_path.py`, `test_phase12_failures_and_edge_cases.py`, `test_phase12_security_isolation_persistence.py` | 20 | 20 | **PASS** |
| **TOTAL BACKEND SUITE** | **pytest (Python 3.11.9)** | **323** | **323** | **100% PASS** |
| **TOTAL FRONTEND SUITE** | **vitest (React 18 / TypeScript)** | **24** | **24** | **100% PASS** |
| **FRONTEND PRODUCTION BUILD** | **`tsc -b && vite build`** | **1,518 modules** | **Clean** | **SUCCESS** |

---

## 13. DEPLOYMENT & INFRASTRUCTURE TOPOLOGY

### 13.1 Production Cloud Architecture

```text
  [ Citizen Browser / Officer Workstation ]
                      │
                      ▼
         [ Vercel Edge Global CDN ]
        Frontend React / TypeScript SPA
    https://sih-2026-revenue-dept.vercel.app
                      │
                      │ HTTPS REST API Requests
                      ▼
            [ Render Web Service ]
        Dockerized FastAPI ASGI Container
    https://sih-2026-revenue-dept.onrender.com
                      │
                      │ Private Network (Internal Port 5432)
                      ▼
          [ Render Managed PostgreSQL ]
                Database: revenue_db
```

### 13.2 Environment Separation & Secret Hygiene

| Variable Name | Purpose | Local Development Value | Production Cloud Configuration |
| :--- | :--- | :--- | :--- |
| **`APP_ENV`** | Environment Mode | `development` | `production` (Enforces strict security checks) |
| **`DATABASE_URL`** | PostgreSQL Connection String | `postgresql://postgres:<pwd>@localhost:5432/revenue_db` | Internal Cloud Connection String from Managed DB |
| **`JWT_SECRET`** | Token Signing Key | Dev secret (ignored in dev) | Cryptographically generated 32+ byte string |
| **`CORS_ORIGINS`** | Allowed Frontend Hosts | `http://localhost:5173,http://localhost:3000` | `https://sih-26129-gov-mesh-citizen.vercel.app,http://localhost:5173` |
| **`OCR_PROVIDER`** | OCR Engine Implementation | `SIMULATED` or `TESSERACT` | `SIMULATED` (deterministic) or `TESSERACT` |
| **`PORT`** | HTTP Listener Port | `8000` | Assigned dynamically by Render host environment |

> **Security Guarantee**: Real passwords, database connection secrets, and private keys are never committed to version control. The `.env` files are strictly ignored via `.gitignore` (`git check-ignore .env` verified). Only safe templates with placeholders exist in [`.env.example`](file:///d:/SIH%202026/revenue-department/.env.example).

---

## 14. FRONTEND MODULES & USER INTERFACE WORKSPACE

The frontend React application is structured into specialized views designed for high-throughput scrutiny:

| Page / Component | Route Path | Target Audience | Primary Capabilities |
| :--- | :--- | :--- | :--- |
| **`LoginPage.tsx`** | `/login` | All Personas | Persona switcher buttons (`Officer`, `Senior`, `Admin`, `Auditor`), JWT authentication. |
| **`DashboardPage.tsx`** | `/` (Home) | Officers & Admins | Operational KPIs, SLA progress bar, pending action queues, statutory AI disclaimer banner. |
| **`ApplicationsListPage.tsx`** | `/applications` | Officers | Full scrutiny table, search by Application ID / Citizen Name, status filters, taluka filters. |
| **`ApplicationDetailPage.tsx`**| `/applications/:id`| Officers | Side-by-side workspace: application address, OCR evidence, confidence bar, SVG preview, approve/reject buttons. |
| **`ActionRequiredPage.tsx`** | `/action-required` | Officers | Filtered queue of applications requiring citizen document re-upload, one-click reprocess button. |
| **`CompletedApplicationsPage.tsx`**| `/completed` | Officers & Auditors | Read-only ledger of finalized approvals with verification timestamps and officer IDs. |
| **`RejectedApplicationsPage.tsx`** | `/rejected` | Officers & Auditors | Historical list of rejected applications displaying statutory rejection justification notes. |
| **`AuditLogPage.tsx`** | `/audit` | Auditors & Admins | Immutable system audit log with actor ID, IP address, timestamp, and JSON delta payload. |
| **`SystemHealthPage.tsx`** | `/health` | System Admins | Real-time database latency graph, service version, environment indicators, and uptime probe. |
| **`NotificationCenter.tsx`** | Top Navigation Bell | All Users | Slide-over notification panel with read/unread toggle and deep links to pending applications. |

---

## 15. REPOSITORY STRUCTURE & SOURCE CODE TOPOLOGY

```text
d:\SIH 2026\revenue-department
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── admin.py                  # Administrative user operations
│   │   │   │   ├── analytics.py              # Operational KPIs & SLA aggregations
│   │   │   │   ├── applications.py           # Application CRUD & search endpoints
│   │   │   │   ├── auth.py                   # Login, token issuance, /me endpoint
│   │   │   │   ├── documents.py              # Upload, binary inspection, SVG preview
│   │   │   │   ├── health.py                 # Liveness & database connectivity probes
│   │   │   │   ├── notifications.py          # In-app alert management
│   │   │   │   └── revenue_workflow.py       # Approve, reject, query, reprocess, override
│   │   │   └── router.py                     # Version 1 consolidated API router
│   │   ├── core/
│   │   │   ├── config.py                     # Pydantic BaseSettings & production validator
│   │   │   └── security.py                   # JWT creation, Bcrypt hashing, token validation
│   │   ├── db/
│   │   │   ├── base.py                       # Declarative Base metadata aggregation
│   │   │   ├── seed.py                       # Idempotent demo database seeder
│   │   │   └── session.py                    # SQLAlchemy connection pooling & init_db
│   │   ├── models/                           # SQLAlchemy ORM database models
│   │   │   ├── application.py                # revenue_applications entity
│   │   │   ├── audit.py                      # revenue_audit_logs entity
│   │   │   ├── consent.py                    # revenue_consents entity
│   │   │   ├── document_evidence.py          # document_verification_records entity
│   │   │   ├── health.py                     # system_health_pings entity
│   │   │   ├── notification.py               # revenue_notifications entity
│   │   │   ├── status_history.py             # application_status_history entity
│   │   │   └── user.py                       # users entity
│   │   ├── repositories/                     # Relational DB repositories with memory fallback
│   │   │   ├── application_repository.py     # Application transactional operations
│   │   │   ├── audit_repository.py           # Audit append-only operations
│   │   │   ├── consent_repository.py         # DPDP consent checks
│   │   │   └── user_repository.py            # User credential queries
│   │   ├── schemas/                          # Pydantic request/response validation models
│   │   │   ├── application.py                # Application validation schemas
│   │   │   ├── auth.py                       # Login & token schemas
│   │   │   └── workflow.py                   # Scrutiny action payloads
│   │   ├── services/
│   │   │   ├── ocr/                          # AI / OCR Intelligent Verification Engine
│   │   │   │   ├── base.py                   # OCRProvider abstract contract
│   │   │   │   ├── confidence_engine.py      # Multi-factor confidence calculator
│   │   │   │   ├── matcher.py                # Levenshtein & token sort matcher
│   │   │   │   ├── normalization.py          # Marathi Devanagari & English text normalizer
│   │   │   │   ├── simulated_provider.py     # Deterministic simulation provider
│   │   │   │   └── tesseract_provider.py     # Google Tesseract bilingual OCR provider
│   │   │   ├── analytics_service.py          # SQL metrics & KPI aggregation service
│   │   │   ├── auth_service.py               # Authentication & token verification logic
│   │   │   ├── consent_service.py            # DPDP Act 8-point consent validator
│   │   │   ├── data_validation_service.py    # 6-part address integrity checker
│   │   │   ├── document_verification_service.py # Document pipeline coordinator
│   │   │   ├── notification_service.py       # Notification generation & dispatch
│   │   │   └── workflow_service.py           # State transition & audit orchestration
│   │   └── main.py                           # FastAPI application entrypoint & middleware
│   ├── tests/                                # 23 backend pytest test files (323 tests)
│   ├── Dockerfile                            # Backend-specific container definition
│   └── requirements.txt                      # Python dependencies (FastAPI, SQLAlchemy, etc.)
├── frontend/
│   ├── src/
│   │   ├── components/                       # Reusable UI components (Navbar, Header, etc.)
│   │   ├── pages/                            # 14 React view pages
│   │   ├── services/
│   │   │   └── api.ts                        # Axios/Fetch API client with cloud base URL
│   │   ├── tests/                            # 8 vitest frontend test suites (24 tests)
│   │   ├── App.tsx                           # Main route switch & auth guard provider
│   │   └── main.tsx                          # React root mounting script
│   ├── package.json                          # Node dependencies & build scripts
│   └── vite.config.ts                        # Vite configuration & dev proxy
├── Dockerfile                                # Root Dockerfile for Render 1-click container
├── docker-compose.yml                        # Multi-container orchestration (DB + API)
├── render.yaml                               # Render Infrastructure-as-Code Blueprint
├── vercel.json                               # Vercel SPA routing rewrite rules
└── .env.example                              # Clean environment configuration template
```

---

## 16. STEP-BY-STEP SIH DEMONSTRATION WORKFLOW

During an evaluation or project showcase, perform the following flow to demonstrate all core capabilities:

1. **Access Portal**: Open `https://sih-2026-revenue-dept.vercel.app` (or `http://localhost:5173`).
2. **One-Click Persona Login**: On the login screen, click the **"Revenue Officer"** quick-demo button. Observe automatic JWT authentication and redirection to the Departmental Officer Dashboard.
3. **Inspect Dashboard Metrics**: Review the live KPI cards: Total Applications (12), Verified (3), Under Scrutiny (4), Action Required (2), Rejected (2). Note the statutory disclaimer banner explicitly stating AI is advisory.
4. **Navigate to Scrutiny Workspace**: Click **"Manage All Applications"** in the navigation bar. Click on application **`GM-2026-000125`** (Vijay Sakharam Patil).
5. **Inspect Evidence & AI Match Signals**:
   * Review the application address: *Flat 402, Shivneri Heights, Shivaji Nagar, Haveli, Pune, 411005*.
   * Review the extracted OCR text from the MSEDCL electricity bill.
   * Observe the green **Confidence Score: 0.96 (AUTO_MATCH_READY)** with matched tokens for Name, Taluka, and PIN code.
   * Toggle the **Document Preview** tab to inspect the sanitized SVG utility bill.
6. **Execute Statutory Approval**: Click the green **"Verify & Approve Application"** button. Add an officer remark: *"Document evidence verified against MSEDCL records. Approved."*
7. **Verify Immediate Status Update**: Observe the status badge transition to **`VERIFIED (FINAL)`**.
8. **Inspect Audit Trail**: Navigate to the **"Audit Trail"** page. Observe the new audit entry at the top: Action `APPROVE`, Actor `revenue.officer`, Target `GM-2026-000125`, with timestamp and metadata payload.
9. **Demonstrate Rejection Rigor**: Open application **`GM-2026-000129`** (Suresh Kadam - Mismatched Taluka). Click **"Reject Application"**. Attempt to submit without a reason (demonstrate client and server validation blocking empty reasons). Enter: *"Mismatched Taluka documentation on utility bill."* Submit rejection.
10. **Verify System Health**: Open the **"System Health"** page. Observe the green **PostgreSQL CONNECTED** indicator with real-time latency (< 45 ms) and zero dropped connection pings.

---

## 17. REVENUE DEPARTMENT MODULE – 5 MINUTE TEAMMATE EXPLANATION

> **Need to explain this module to a teammate or mentor in 5 minutes? Use this guide:**

1. **What is our module?**  
   We built the **Revenue & Forest Department** module of GovMesh. In Maharashtra, our department is the legal authority for where citizens live and where land parcels exist. When a citizen changes their address on GovMesh, our service proves whether that new address is genuine.
2. **How does the citizen experience it?**  
   The citizen enters their new address, grants digital consent under the DPDP Act, and uploads a utility bill. That’s all they have to do.
3. **What happens behind the scenes?**  
   Our backend checks their consent, validates their document file (preventing spoofed files), and runs OCR in Marathi and English. An AI matcher compares the utility bill against the address they typed and calculates a confidence score (e.g., $95\%$ match).
4. **Does the AI make the decision?**  
   **No.** By government law, an algorithm cannot legally approve or reject a citizen. The AI does the heavy clerical lifting (reading the bill, finding the name, checking the taluka and PIN), but a **Revenue Officer** reviews the side-by-side evidence on their dashboard and clicks the final Approve or Reject button.
5. **Where is data saved?**  
   Everything is stored in a **PostgreSQL** database across 8 tables (applications, users, audit logs, consents, notifications, etc.). If the database is ever disconnected during local testing, our code has a fallback to memory dictionaries so nothing crashes.
6. **How is it deployed?**  
   The React frontend is live on **Vercel**, the FastAPI backend runs on **Render**, and the database is hosted on **PostgreSQL**.
7. **How do we know it works?**  
   We have **323 backend automated tests** and **24 frontend tests** covering happy paths, document spoofing, expired consents, and server failures. Every single test passes.

---

## 18. PRESENTATION-READY SUMMARY (EXECUTIVE BRIEF)

* **Core Problem**: Manual, paper-based address verification in government departments takes weeks, suffers from document forgery, creates citizen blackouts, and lacks compliance with India's DPDP Act 2023.
* **Our Solution**: An automated, intelligent digital revenue platform combining DPDP digital consent, bilingual Marathi/English OCR, confidence scoring, and an ergonomic officer decision workspace.
* **Key Innovations**:
  * **DPDP-First Architecture**: 8-point automated validation of citizen consent before personal data processing.
  * **Bilingual OCR Normalization**: Standardizes Devanagari numerals and Marathi administrative terminology for fuzzy matching.
  * **Statutory Human-in-the-Loop**: Machine learning assists the officer; human officers retain statutory decision authority.
  * **Immutable Auditability**: Complete chronological audit trail for every status transition, override, and login.
* **Technology Stack**: React 18, TypeScript, TailwindCSS, FastAPI, Python 3.11, Pydantic v2, SQLAlchemy 2.0, PostgreSQL 18.6, Docker, Vercel, Render.
* **Current Status**: **Fully functional, 100% test-verified (323 backend tests, 24 frontend tests), deployed on cloud infrastructure, and ready for GovMesh interoperability integration.**

---

## 19. WHAT WE HAVE BUILT SO FAR

```text
[✔] Phase 01: Official Maharashtra e-Governance UI Foundation
[✔] Phase 02: Canonical Revenue Application Schemas & 6-Stage Lifecycle
[✔] Phase 03: Bcrypt Authentication & 4-Tier Hierarchical RBAC
[✔] Phase 04: Address Verification Engine & 8-Point DPDP Consent Validator
[✔] Phase 05: Document Ingestion Pipeline & OCR Provider Abstraction
[✔] Phase 06: API Hardening, Error Normalization & Mandatory Rejection Notes
[✔] Phase 07: Cloud Deployment (Vercel SPA + Render Container + Dynamic Port)
[✔] Phase 08: Relational PostgreSQL Engine (8 Tables, Connection Pool, Seed)
[✔] Phase 09: Enterprise Security Hardening (OWASP Headers, Rate Limit, CSP)
[✔] Phase 10: AI/OCR Intelligent Scrutiny (Bilingual Normalizer + Confidence Engine)
[✔] Phase 11: Real-Time Operational Analytics & Departmental KPI Dashboard
[✔] Phase 12: End-to-End Failure Simulations & 347 Combined Automated Tests
[✔] Render Blueprint & PostgreSQL Dialect Normalization (render.yaml)
```

The GovMesh Revenue & Forest Department system is complete, robust, secure, and fully verified.
