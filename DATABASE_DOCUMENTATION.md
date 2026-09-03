# GovMesh SIH26129 — Revenue & Forest Department Database Documentation

This document serves as the authoritative technical reference for the internal database architecture, ORM models, SQL DDL specifications, and persistence contracts of the Revenue & Forest Department backend service.

---

## 1. Database Architecture Overview

* **Target Database Engine**: PostgreSQL 16
* **Database Name**: `revenue_db`
* **Default Port**: `5432`
* **ORM Layer**: SQLAlchemy 2.0 (`sqlalchemy>=2.0.28,<3.0.0`)
* **Python Database Driver**: `psycopg2-binary` (synchronous connection pooling via `create_engine`)
* **Execution Strategy**: Fault-Tolerant Hybrid Model
  * **Primary (Active)**: SQLAlchemy ORM transactions directly connected to PostgreSQL.
  * **Fallback (Standalone/Serverless)**: In-memory synchronized store initialized from statutory synthetic seed data when the database is unavailable or operating in serverless environments (e.g. Vercel).

---

## 2. Department Database Tables & Schema

The Revenue Department system defines **7 core tables**:

### 1. `system_health_pings`
Lightweight health verification and read/write probe table.
* **Columns**:
  * `id` (`SERIAL` / `INTEGER`, Primary Key, autoincrement)
  * `service_name` (`VARCHAR(100)`, NOT NULL, Default: `'revenue-department'`)
  * `ping_type` (`VARCHAR(50)`, NOT NULL, Default: `'startup_check'`)
  * `created_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
* **Indexes**: `system_health_pings_pkey` on `id`.

---

### 2. `users`
Departmental officer accounts, administrative roles, and RBAC authentication data.
* **Columns**:
  * `id` (`VARCHAR(50)`, Primary Key)
  * `username` (`VARCHAR(100)`, UNIQUE, NOT NULL)
  * `email` (`VARCHAR(255)`, UNIQUE, NOT NULL)
  * `mobile` (`VARCHAR(20)`, UNIQUE, NOT NULL)
  * `password_hash` (`VARCHAR(255)`, NOT NULL)
  * `full_name` (`VARCHAR(255)`, NOT NULL)
  * `role` (`VARCHAR(50)`, NOT NULL) — *e.g., `REVENUE_OFFICER`, `SENIOR_REVENUE_OFFICER`, `DEPARTMENT_ADMINISTRATOR`, `READ_ONLY_AUDITOR`*
  * `department` (`VARCHAR(100)`, NOT NULL, Default: `'Revenue & Forest Department'`)
  * `division` (`VARCHAR(100)`, NOT NULL, Default: `'Pune Division'`)
  * `is_active` (`BOOLEAN`, NOT NULL, Default: `TRUE`)
  * `created_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `updated_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `last_login_at` (`TIMESTAMP WITH TIME ZONE`, Nullable)
  * `failed_login_attempts` (`INTEGER`, NOT NULL, Default: `0`)
  * `locked_until` (`TIMESTAMP WITH TIME ZONE`, Nullable)
* **Indexes**:
  * `idx_users_username` on `username` (UNIQUE)
  * `idx_users_email` on `email` (UNIQUE)
  * `idx_users_mobile` on `mobile` (UNIQUE)
  * `idx_users_role` on `role`

---

### 3. `revenue_applications`
Core departmental records for citizen address change and land registry linkage applications.
* **Columns**:
  * `id` (`VARCHAR(50)`, Primary Key)
  * `application_id` (`VARCHAR(50)`, UNIQUE, NOT NULL) — *e.g., `GM-2026-000124`*
  * `correlation_id` (`VARCHAR(100)`, NOT NULL)
  * `citizen_reference_id` (`VARCHAR(50)`, NOT NULL)
  * `service_type` (`VARCHAR(50)`, NOT NULL, Default: `'ADDRESS_CHANGE'`)
  * `requested_operation` (`VARCHAR(100)`, NOT NULL, Default: `'UPDATE_REVENUE_ADDRESS'`)
  * `purpose` (`VARCHAR(255)`, NOT NULL)
  * `consent_reference` (`VARCHAR(100)`, NOT NULL)
  * `priority` (`VARCHAR(20)`, NOT NULL, Default: `'NORMAL'`)
  * `status` (`VARCHAR(30)`, NOT NULL, Default: `'PENDING'`)
  * `required_action` (`VARCHAR(255)`, NOT NULL)
  * `citizen_name` (`VARCHAR(255)`, NOT NULL)
  * `received_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `updated_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `processing_started_at` (`TIMESTAMP WITH TIME ZONE`, Nullable)
  * `completed_at` (`TIMESTAMP WITH TIME ZONE`, Nullable)
  * `assigned_officer_id` (`VARCHAR(50)`, Nullable)
  * `data_payload` (`JSON` / `JSONB`, NOT NULL) — *Contains structured `existing_address`, `new_address`, and `proof_documents`*
  * `workflow_history` (`JSON` / `JSONB`, NOT NULL) — *Contains chronological milestone audit events*
* **Indexes**:
  * `idx_apps_application_id` on `application_id` (UNIQUE)
  * `idx_apps_correlation_id` on `correlation_id`
  * `idx_apps_citizen_ref` on `citizen_reference_id`
  * `idx_apps_status` on `status`
  * `idx_apps_priority` on `priority`
  * `idx_apps_service_type` on `service_type`
  * `idx_apps_received_at` on `received_at DESC`

---

### 4. `revenue_consents`
Citizen Digital Personal Data Protection (DPDP) legal consent artifacts.
* **Columns**:
  * `id` (`VARCHAR(50)`, Primary Key)
  * `consent_reference` (`VARCHAR(100)`, UNIQUE, NOT NULL) — *e.g., `CONSENT-2026-00124`*
  * `application_id` (`VARCHAR(50)`, NOT NULL)
  * `status` (`VARCHAR(30)`, NOT NULL, Default: `'VALID'`)
  * `purpose` (`VARCHAR(255)`, NOT NULL)
  * `data_scope` (`VARCHAR(255)`, NOT NULL)
  * `recipient` (`VARCHAR(255)`, NOT NULL)
  * `issued_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `expires_at` (`TIMESTAMP WITH TIME ZONE`, NOT NULL)
  * `revoked_at` (`TIMESTAMP WITH TIME ZONE`, Nullable)
  * `validated_at` (`TIMESTAMP WITH TIME ZONE`, Nullable)
  * `validation_result` (`JSON` / `JSONB`, Nullable)
* **Indexes**:
  * `idx_consents_reference` on `consent_reference` (UNIQUE)
  * `idx_consents_app_id` on `application_id`
  * `idx_consents_status` on `status`

---

### 5. `revenue_audit_logs`
Immutable, append-only departmental audit log of all officer scrutiny decisions, approvals, rejections, and state changes.
* **Columns**:
  * `id` (`VARCHAR(50)`, Primary Key)
  * `officer_id` (`VARCHAR(50)`, NOT NULL)
  * `officer_name` (`VARCHAR(255)`, NOT NULL)
  * `application_id` (`VARCHAR(50)`, NOT NULL)
  * `action` (`VARCHAR(50)`, NOT NULL) — *e.g., `START_REVIEW`, `APPROVE`, `REJECT`, `REQUEST_INFORMATION`, `REPROCESS`, `RETRY`*
  * `previous_status` (`VARCHAR(30)`, Nullable)
  * `new_status` (`VARCHAR(30)`, NOT NULL)
  * `reason` (`VARCHAR(1000)`, Nullable)
  * `correlation_id` (`VARCHAR(100)`, NOT NULL)
  * `timestamp` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `details` (`JSON` / `JSONB`, Nullable)
* **Indexes**:
  * `idx_audit_officer_id` on `officer_id`
  * `idx_audit_app_id` on `application_id`
  * `idx_audit_action` on `action`
  * `idx_audit_timestamp` on `timestamp DESC`

---

### 6. `application_status_history`
Chronological state transition tracking for application timeline reconstruction.
* **Columns**:
  * `id` (`VARCHAR(50)`, Primary Key)
  * `application_id` (`VARCHAR(50)`, NOT NULL)
  * `previous_status` (`VARCHAR(30)`, Nullable)
  * `new_status` (`VARCHAR(30)`, NOT NULL)
  * `action` (`VARCHAR(50)`, NOT NULL)
  * `changed_by` (`VARCHAR(255)`, NOT NULL)
  * `reason` (`VARCHAR(1000)`, Nullable)
  * `timestamp` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `correlation_id` (`VARCHAR(100)`, NOT NULL)
* **Indexes**:
  * `idx_history_app_id` on `application_id`
  * `idx_history_timestamp` on `timestamp DESC`

---

### 7. `revenue_notifications`
Internal departmental notices, citizen query alerts, escalation notices, and milestone dispatches.
* **Columns**:
  * `id` (`VARCHAR(50)`, Primary Key)
  * `type` (`VARCHAR(50)`, NOT NULL) — *e.g., `NEW_APPLICATION`, `ACTION_REQUIRED`, `CITIZEN_RESPONSE`, `WORKFLOW_COMPLETION`, `ESCALATION`*
  * `application_id` (`VARCHAR(50)`, NOT NULL)
  * `title` (`VARCHAR(255)`, NOT NULL)
  * `message` (`VARCHAR(1000)`, NOT NULL)
  * `timestamp` (`TIMESTAMP WITH TIME ZONE`, NOT NULL, Default: `CURRENT_TIMESTAMP`)
  * `read` (`BOOLEAN`, NOT NULL, Default: `FALSE`)
  * `severity` (`VARCHAR(20)`, NOT NULL, Default: `'INFO'`) — *`INFO`, `WARNING`, `CRITICAL`, `SUCCESS`*
  * `target_role` (`VARCHAR(50)`, NOT NULL, Default: `'ALL'`)
* **Indexes**:
  * `idx_notif_type` on `type`
  * `idx_notif_app_id` on `application_id`
  * `idx_notif_timestamp` on `timestamp DESC`
  * `idx_notif_read` on `read`
  * `idx_notif_target_role` on `target_role`

---

## 3. Important Domain Relationships

* **`revenue_applications` ↔ `users`**: Logical foreign key via `assigned_officer_id` referencing `users(id)`.
* **`revenue_applications` ↔ `revenue_consents`**: Linked via `consent_reference` (`revenue_applications.consent_reference = revenue_consents.consent_reference`) and `application_id`.
* **`revenue_applications` ↔ `revenue_audit_logs`**: One-to-many relationship linking every state change in `revenue_applications(application_id)` to immutable records in `revenue_audit_logs(application_id)`.
* **`revenue_applications` ↔ `application_status_history`**: One-to-many relationship linking status progressions to `application_status_history(application_id)`.
* **`revenue_applications` ↔ `revenue_notifications`**: One-to-many relationship linking notifications to `revenue_notifications(application_id)`.

---

## 4. Current Schema Initialization Methods

The database schema is initialized using two complementary mechanisms:
1. **Automated Application Startup (`init_db`)**:
   During FastAPI lifespan startup (`app/main.py`), `init_db()` invokes `Base.metadata.create_all(bind=engine)` after importing all ORM models.
2. **Raw DDL Initialization Script (`database/init-db.sql`)**:
   Can be executed directly via `psql` or mounted inside container initialization (`/docker-entrypoint-initdb.d/init-db.sql`) to establish the PostgreSQL baseline schema and index structures.

---

## 5. `Base.metadata.create_all()` Limitations

> [!WARNING]
> `Base.metadata.create_all()` is **NOT** a database migration engine:
> * It only creates tables and indexes that **do not already exist** in the target database.
> * It **cannot** detect or alter modified columns, renamed fields, changed constraints, or dropped columns.
> * It does not support reversible versioning, rollbacks, or tracking of historical schema revisions.

---

## 6. Migration Status & Roadmap

* **Current Migration System**: **None** (Explicit schema creation via `create_all()` and `database/init-db.sql`).
* **Future Recommendation**:
  * Implement **Alembic** (`alembic>=1.13.0`) in a subsequent development step to manage automated schema revisions, migration history (`alembic_version` table), and repeatable continuous integration migrations across staging and production.

---

## 7. PostgreSQL Seeding & Deterministic Demo Dataset

### Overview

The application includes an idempotent database seeder (`backend/app/db/seed.py`) designed to populate PostgreSQL (`revenue_db`) with deterministic synthetic records required for local development, demonstration, and automated integration tests.

The seeder is automatically invoked on application startup via `init_db()`, and can also be triggered directly as a CLI script:

```bash
python backend/app/db/seed.py
```

### Seeded Entities Summary

| Entity Model | Target Table | Seeded Count | Description |
| :--- | :--- | :--- | :--- |
| **User** | `users` | 5 | 5 departmental accounts covering full RBAC hierarchy with bcrypt password hashes. |
| **Application** | `revenue_applications` | 12 | 12 synthetic Maharashtra address-change applications across all workflow states. |
| **ConsentRecord** | `revenue_consents` | 12 | 12 DPDP Act compliant consent records linked to applications. |
| **Notification** | `revenue_notifications` | 5 | Baseline departmental notices and alerts. |
| **AuditLog** | `revenue_audit_logs` | 12+ | Baseline immutable audit trail records for seeded applications. |
| **ApplicationStatusHistory** | `application_status_history` | 12+ | Baseline status history entries tracking milestone progressions. |

### Demo Officer Accounts

| User ID | Username | Role (`RoleEnum`) | Full Name | Department / Division | Test Password |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `USR-REV-001` | `revenue.officer` | `REVENUE_OFFICER` | Rajendra Mane (Revenue Officer) | Pune Division (Haveli Tahsil) | `Officer@2026` |
| `USR-REV-002` | `senior.officer` | `SENIOR_REVENUE_OFFICER` | Dr. Sunita Bhosale (Senior Officer / Tahsildar) | Pune Division (District Collectorate) | `Senior@2026` |
| `USR-REV-003` | `revenue.admin` | `DEPARTMENT_ADMINISTRATOR` | Amit Kulkarni (Department Administrator) | State Headquarters (Mantralaya) | `Admin@2026` |
| `USR-REV-004` | `revenue.auditor` | `READ_ONLY_AUDITOR` | Meera Deshpande (State Revenue Auditor) | State Revenue Audit Directorate | `Auditor@2026` |
| `USR-REV-005` | `inactive.officer` | `REVENUE_OFFICER` (*Deactivated*) | Inactive Officer Account (Test) | Suspended Desk | `Inactive@2026` |

### Synthetic Applications Dataset Distribution

* **Total Applications**: 12 (`APP-REV-001` to `APP-REV-012` / `GM-2026-000124` to `GM-2026-000135`)
* **Workflow Status Breakdown**:
  * `PENDING`: 4 applications
  * `PROCESSING`: 4 applications
  * `VERIFIED`: 2 applications
  * `ACTION_REQUIRED`: 1 application
  * `QUEUED`: 1 application
* **Priority Breakdown**: `HIGH` (5), `NORMAL` (4), `LOW` (2), `URGENT` (1)
* **Districts & Jurisdictions**: Pune, Satara, Solapur, Nashik, Kolhapur, Nagpur, and Mumbai Suburban.
* **Proof Document Simulation**: Valid Electricity Bills, Municipal Tax Receipts, Registered Rent Agreements, Property Card / 7-12 Extracts, and edge-case mismatched/corrupt documents.

### Idempotency & Safety Guarantees

* The seeder checks for existing primary keys (`users.id`, `users.username`, `revenue_applications.application_id`, `revenue_consents.consent_reference`, `revenue_notifications.id`) before inserting records.
* Subsequent executions create `0` duplicates and preserve existing database modifications.
* When executing automated test suites, `conftest.py` utilizes a module-scoped fixture to reset the synthetic test applications to their baseline states for clean, repeatable test isolation.

---

## 8. Repository Persistence & Transactional Hardening

### Overview

The data access layer is structured into specialized repositories that interact directly with PostgreSQL via SQLAlchemy ORM, supported by a synchronized in-memory fallback store for standalone execution.

### Repository Operations Matrix

| Layer | Method | PostgreSQL Table | DB Action | Transaction Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`ApplicationRepository`** | `get_by_application_id` | `revenue_applications` | `SELECT` | Read-only |
| **`ApplicationRepository`** | `get_all_applications` | `revenue_applications` | `SELECT` | Read-only |
| **`ApplicationRepository`** | `list_applications` | `revenue_applications` | `SELECT` (paginated) | Read-only |
| **`ApplicationRepository`** | `get_dashboard_summary` | `revenue_applications` | `SELECT` (aggregate) | Read-only |
| **`ApplicationRepository`** | `update_application_status` | `revenue_applications` | `UPDATE` | Flush or Commit |
| **`ApplicationRepository`** | `append_workflow_event` | `revenue_applications` (`workflow_history`) | `UPDATE` (JSONB) | Flush or Commit |
| **`ApplicationRepository`** | `attach_document` | `revenue_applications` (`data_payload`) | `UPDATE` (JSONB) | Auto-commit |
| **`ApplicationRepository`** | `override_document` | `revenue_applications` (`data_payload`) | `UPDATE` (JSONB) | Auto-commit |
| **`AuditRepository`** | `create_audit_entry` | `revenue_audit_logs` | `INSERT` | Flush or Commit |
| **`AuditRepository`** | `record_status_history` | `application_status_history` | `INSERT` | Flush or Commit |
| **`AuditRepository`** | `list_audit_logs` | `revenue_audit_logs` | `SELECT` (paginated) | Read-only |
| **`NotificationRepository`** | `create_notification` | `revenue_notifications` | `INSERT` | Auto-commit |
| **`NotificationRepository`** | `list_notifications` | `revenue_notifications` | `SELECT` | Read-only |
| **`NotificationRepository`** | `mark_as_read` | `revenue_notifications` | `UPDATE` | Auto-commit |
| **`UserRepository`** | `get_by_identifier` | `users` | `SELECT` | Read-only |
| **`UserRepository`** | `update_last_login` | `users` | `UPDATE` | Auto-commit |

### Transaction Management & Unit of Work

1. **Request-Scoped Session Sharing**:
   FastAPI's dependency injection (`Depends(get_db)`) shares a single database session across all repositories within an incoming HTTP request.
2. **Explicit Rollback on Exception**:
   The `get_db()` generator in `backend/app/db/session.py` encapsulates the session yield in a `try...except...finally` block. Any uncaught exception triggers an immediate `db.rollback()` before connection closure, preventing dirty transaction state leaks into the connection pool.
3. **Multi-Table Workflow Atomicity**:
   When `WorkflowService` processes a state change (`start_review`, `approve_application`, `reject_application`, `request_additional_information`, `reprocess_application`, `retry_application`), child repository calls (`update_application_status`, `append_workflow_event`, `record_status_history`, `create_audit_entry`) execute with `auto_commit=False` (flushing modifications to the database). The outer service commits once upon successful completion of all operations. If an exception occurs at any point, `session.rollback()` rolls back the entire set of mutations.
4. **JSONB Mutation Tracking**:
   PostgreSQL JSONB columns (`data_payload`, `workflow_history`) utilize SQLAlchemy's `flag_modified(db_app, "column_name")` upon in-place list/dict mutations to guarantee that ORM change trackers register the update prior to flush/commit.
5. **Decoupled Notifications**:
   Internal notifications (`_emit_notif`) are dispatched after transaction commit, ensuring that notification failures never roll back authoritative application decisions.

---

## 9. PostgreSQL End-to-End Verification

### Overview

Phase 08 — Step 06 executed comprehensive end-to-end verification against the PostgreSQL database (`revenue_db`), exercising the entire system flow across all layers:

$$\text{HTTP API} \longrightarrow \text{FastAPI Router} \longrightarrow \text{RBAC Auth} \longrightarrow \text{Service Layer} \longrightarrow \text{Repository Layer} \longrightarrow \text{PostgreSQL} \longrightarrow \text{Commit} \longrightarrow \text{Fresh Session Read}$$

### Verification Scope & Flow Coverage

| Area | Verification Scope | Status | Notes |
| :--- | :--- | :---: | :--- |
| **PostgreSQL Connectivity** | `/health`, `/health/db`, raw SQL execution | ✅ | Verified live connection and query execution. |
| **Authentication & RBAC** | All 5 seeded roles (`officer`, `senior`, `admin`, `auditor`, `inactive`) | ✅ | Inactive accounts blocked (403); Auditor blocked from mutations. |
| **Application Listing** | Filtering by status, priority, and text search | ✅ | Exact match with 12 seeded PostgreSQL applications. |
| **Application Detail** | Full schema (`data_payload`, `workflow_history`) | ✅ | Matches `revenue_applications` row. |
| **Dashboard Aggregates** | Total, pending, processing, verified, rejected | ✅ | Cross-checked against direct SQL `COUNT(*)` queries. |
| **Start Review Workflow** | `PENDING` $\rightarrow$ `PROCESSING` state transition | ✅ | Status, timestamp, officer assignment committed. |
| **Approval Workflow** | `PROCESSING` $\rightarrow$ `VERIFIED` with reason | ✅ | Status history, audit entry, and notification generated. |
| **Rejection Workflow** | `PROCESSING` $\rightarrow$ `REJECTED` with reason | ✅ | Rejection reason, audit log, and status history persisted. |
| **Additional Information** | `ACTION_REQUIRED` query transition | ✅ | Query payload, action notes, and audit record committed. |
| **Reprocess Workflow** | `ACTION_REQUIRED` $\rightarrow$ `PROCESSING` | ✅ | Chronological timeline event recorded. |
| **Controlled Retry** | Phase 05 operational retry recovery | ✅ | Resumes scrutiny without record duplication. |
| **Document JSONB** | Document attachment and officer override | ✅ | Validates `flag_modified()` JSONB persistence. |
| **DPDP Citizen Consent** | Valid, expired, and revoked consent checks | ✅ | Expired consent blocks approval (HTTP 422). |
| **Immutable Audit Logs** | Paginated audit trail retrieval | ✅ | Immutable audit records; GET requests produce 0 duplicates. |
| **Status History** | Full chronological lifecycle timeline | ✅ | Status history preserves transition order and actors. |
| **Department Notifications**| List, unread count, mark-read, mark-all-read | ✅ | Notifications persisted in `revenue_notifications`. |
| **Transaction Rollback** | Mid-operation exception injection | ✅ | Verified 0 partial commits / dirty state on failure. |
| **Session Isolation** | Independent session mutation visibility | ✅ | Committed state immediately visible to fresh sessions. |
| **Restart Persistence** | Session teardown and reconnection | ✅ | Mutations survive session closure and reconnection. |
| **API $\leftrightarrow$ DB Consistency** | Direct SQL comparison against API JSON | ✅ | 100% column-level match confirmed. |

### Test Execution & Results

```bash
python -m pytest -o pythonpath=. backend/tests
```

**Final Suite Metrics**:
* **Total Tests**: `121` (93 baseline + 11 persistence + 17 PostgreSQL E2E)
* **Passed**: `121`
* **Failed**: `0`
* **Warnings**: `10` (deprecation notices)
* **Execution Time**: `~71s`

### PostgreSQL Environment Parameters
* **Target Engine**: PostgreSQL 16
* **Database**: `revenue_db`
* **Connection Pool**: 5 connections (`DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10`)
* **Authoritative Schema**: `system_health_pings`, `users`, `revenue_applications`, `revenue_consents`, `revenue_audit_logs`, `application_status_history`, `revenue_notifications`

### Known Limitations
* **Standalone / Serverless Mode**: When deployed in serverless environments without direct PostgreSQL access (e.g., edge runtimes), the system gracefully operates on its synchronized in-memory fallback store initialized from the deterministic seed dataset.



