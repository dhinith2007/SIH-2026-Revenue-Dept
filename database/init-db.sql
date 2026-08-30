-- ============================================================================
-- GovMesh SIH26129: Revenue & Forest Department Database Initializer (Phase 01, 02, 03 & 04)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Minimal health tracking table to verify read/write database readiness
CREATE TABLE IF NOT EXISTS system_health_pings (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL DEFAULT 'revenue-department',
    ping_type VARCHAR(50) NOT NULL DEFAULT 'startup_check',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed an initial health verification entry
INSERT INTO system_health_pings (service_name, ping_type)
VALUES ('revenue-department', 'initial_database_seed')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Phase 02: Department Users & RBAC Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    mobile VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL DEFAULT 'Revenue & Forest Department',
    division VARCHAR(100) NOT NULL DEFAULT 'Pune Division',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- Phase 03: Revenue Applications Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS revenue_applications (
    id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50) UNIQUE NOT NULL,
    correlation_id VARCHAR(100) NOT NULL,
    citizen_reference_id VARCHAR(50) NOT NULL,
    service_type VARCHAR(50) NOT NULL DEFAULT 'ADDRESS_CHANGE',
    requested_operation VARCHAR(100) NOT NULL DEFAULT 'UPDATE_REVENUE_ADDRESS',
    purpose VARCHAR(255) NOT NULL,
    consent_reference VARCHAR(100) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'NORMAL',
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    required_action VARCHAR(255) NOT NULL,
    citizen_name VARCHAR(255) NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    assigned_officer_id VARCHAR(50),
    data_payload JSONB NOT NULL,
    workflow_history JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_apps_application_id ON revenue_applications(application_id);
CREATE INDEX IF NOT EXISTS idx_apps_correlation_id ON revenue_applications(correlation_id);
CREATE INDEX IF NOT EXISTS idx_apps_citizen_ref ON revenue_applications(citizen_reference_id);
CREATE INDEX IF NOT EXISTS idx_apps_status ON revenue_applications(status);
CREATE INDEX IF NOT EXISTS idx_apps_priority ON revenue_applications(priority);
CREATE INDEX IF NOT EXISTS idx_apps_service_type ON revenue_applications(service_type);
CREATE INDEX IF NOT EXISTS idx_apps_received_at ON revenue_applications(received_at DESC);

-- ============================================================================
-- Phase 04: Legal Consents Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS revenue_consents (
    id VARCHAR(50) PRIMARY KEY,
    consent_reference VARCHAR(100) UNIQUE NOT NULL,
    application_id VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'VALID',
    purpose VARCHAR(255) NOT NULL,
    data_scope VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    validated_at TIMESTAMP WITH TIME ZONE,
    validation_result JSONB
);

CREATE INDEX IF NOT EXISTS idx_consents_reference ON revenue_consents(consent_reference);
CREATE INDEX IF NOT EXISTS idx_consents_app_id ON revenue_consents(application_id);
CREATE INDEX IF NOT EXISTS idx_consents_status ON revenue_consents(status);

-- ============================================================================
-- Phase 04: Departmental Audit Logs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS revenue_audit_logs (
    id VARCHAR(50) PRIMARY KEY,
    officer_id VARCHAR(50) NOT NULL,
    officer_name VARCHAR(255) NOT NULL,
    application_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    reason VARCHAR(1000),
    correlation_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_officer_id ON revenue_audit_logs(officer_id);
CREATE INDEX IF NOT EXISTS idx_audit_app_id ON revenue_audit_logs(application_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON revenue_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON revenue_audit_logs(timestamp DESC);

-- ============================================================================
-- Phase 04: Application Status History Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS application_status_history (
    id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50) NOT NULL,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    action VARCHAR(50) NOT NULL,
    changed_by VARCHAR(255) NOT NULL,
    reason VARCHAR(1000),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    correlation_id VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_app_id ON application_status_history(application_id);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON application_status_history(timestamp DESC);
