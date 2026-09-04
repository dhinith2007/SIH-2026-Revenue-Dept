from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.application import Application
from app.db.seed_applications import get_seeded_applications
from app.core.logging import logger

_MEM_APPLICATIONS: Dict[str, Dict[str, Any]] = {}
_LAST_DB_CHECK_FAILED: float = 0.0
_DB_RETRY_INTERVAL_SECONDS: float = 30.0


def _init_memory_store():
    global _MEM_APPLICATIONS
    if not _MEM_APPLICATIONS:
        seeded = get_seeded_applications()
        for app in seeded:
            _MEM_APPLICATIONS[app["application_id"]] = app


_init_memory_store()


class ApplicationRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        _init_memory_store()

    def _should_skip_db(self) -> bool:
        global _LAST_DB_CHECK_FAILED
        if _LAST_DB_CHECK_FAILED > 0:
            if time.time() - _LAST_DB_CHECK_FAILED < _DB_RETRY_INTERVAL_SECONDS:
                return True
        return False

    def _mark_db_failed(self):
        global _LAST_DB_CHECK_FAILED
        _LAST_DB_CHECK_FAILED = time.time()

    def get_by_application_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Finds application by its unique application_id (e.g. GM-2026-000124)."""
        clean_id = application_id.strip()
        if self.db and not self._should_skip_db():
            try:
                app = self.db.query(Application).filter(Application.application_id == clean_id).first()
                if app:
                    return self._to_dict(app)
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_by_application_id, using memory store: %s", exc)

        return _MEM_APPLICATIONS.get(clean_id)

    def get_all_applications(self) -> List[Dict[str, Any]]:
        """Retrieves all application records for consistency and duplicate verification."""
        if self.db and not self._should_skip_db():
            try:
                db_apps = self.db.query(Application).all()
                if db_apps:
                    return [self._to_dict(a) for a in db_apps]
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_all_applications, using memory store: %s", exc)
        return list(_MEM_APPLICATIONS.values())

    def update_application_status(
        self,
        application_id: str,
        new_status: str,
        assigned_officer_id: Optional[str] = None,
        processing_started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        required_action: Optional[str] = None,
        auto_commit: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates application lifecycle status and timestamps.
        """
        clean_id = application_id.strip()
        now = datetime.now(timezone.utc)

        # Update in-memory record
        if clean_id in _MEM_APPLICATIONS:
            rec = _MEM_APPLICATIONS[clean_id]
            rec["status"] = new_status
            rec["updated_at"] = now
            if assigned_officer_id:
                rec["assigned_officer_id"] = assigned_officer_id
            if processing_started_at:
                rec["processing_started_at"] = processing_started_at
            if completed_at:
                rec["completed_at"] = completed_at
            if required_action:
                rec["required_action"] = required_action

        # Update PostgreSQL if connected
        if self.db and not self._should_skip_db():
            try:
                db_app = self.db.query(Application).filter(Application.application_id == clean_id).first()
                if db_app:
                    db_app.status = new_status
                    db_app.updated_at = now
                    if assigned_officer_id:
                        db_app.assigned_officer_id = assigned_officer_id
                    if processing_started_at:
                        db_app.processing_started_at = processing_started_at
                    if completed_at:
                        db_app.completed_at = completed_at
                    if required_action:
                        db_app.required_action = required_action
                    if auto_commit:
                        self.db.commit()
                    else:
                        self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                    self._mark_db_failed()
                    logger.warning("DB update failed in update_application_status: %s", exc)
                else:
                    raise

        return self.get_by_application_id(clean_id)

    def append_workflow_event(
        self, application_id: str, event: Dict[str, Any], auto_commit: bool = True
    ) -> None:
        """Appends a workflow milestone to the application's internal history payload."""
        clean_id = application_id.strip()
        if clean_id in _MEM_APPLICATIONS:
            rec = _MEM_APPLICATIONS[clean_id]
            if "workflow_history" not in rec or not isinstance(rec["workflow_history"], list):
                rec["workflow_history"] = []
            rec["workflow_history"].append(event)

        if self.db and not self._should_skip_db():
            try:
                db_app = self.db.query(Application).filter(Application.application_id == clean_id).first()
                if db_app:
                    history = list(db_app.workflow_history or [])
                    history.append(event)
                    db_app.workflow_history = history
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(db_app, "workflow_history")
                    if auto_commit:
                        self.db.commit()
                    else:
                        self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                    self._mark_db_failed()
                    logger.warning("DB update failed in append_workflow_event: %s", exc)
                else:
                    raise

    def list_applications(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        service_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "received_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        all_items = list(_MEM_APPLICATIONS.values())

        # Whitelist sorting parameter to prevent arbitrary attribute exposure (SEC-05 / Domain 5)
        ALLOWED_SORT_COLUMNS = {
            "received_at",
            "updated_at",
            "priority",
            "status",
            "citizen_name",
            "application_id",
            "service_type",
        }
        clean_sort_by = (sort_by or "received_at").strip().lower()
        if clean_sort_by not in ALLOWED_SORT_COLUMNS:
            clean_sort_by = "received_at"

        if self.db and not self._should_skip_db():
            try:
                query = self.db.query(Application)
                if status and status.upper() != "ALL":
                    query = query.filter(Application.status == status.upper())
                if priority and priority.upper() != "ALL":
                    query = query.filter(Application.priority == priority.upper())
                if service_type and service_type.upper() != "ALL":
                    query = query.filter(Application.service_type == service_type.upper())
                if search and search.strip():
                    term = f"%{search.strip()}%"
                    query = query.filter(
                        (Application.application_id.ilike(term))
                        | (Application.correlation_id.ilike(term))
                        | (Application.citizen_reference_id.ilike(term))
                        | (Application.citizen_name.ilike(term))
                    )

                total = query.count()
                sort_col = getattr(Application, clean_sort_by, Application.received_at)
                if sort_order.lower() == "asc":
                    query = query.order_by(sort_col.asc())
                else:
                    query = query.order_by(sort_col.desc())

                offset = (page - 1) * page_size
                db_results = query.offset(offset).limit(page_size).all()
                total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                items = [self._to_summary_dict(self._to_dict(a)) for a in db_results]
                return items, total, total_pages
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in list_applications, falling back to memory store: %s", exc)

        # In-memory filtering & search
        filtered = all_items
        if status and status.upper() != "ALL":
            filtered = [a for a in filtered if a["status"] == status.upper()]
        if priority and priority.upper() != "ALL":
            filtered = [a for a in filtered if a["priority"] == priority.upper()]
        if service_type and service_type.upper() != "ALL":
            filtered = [a for a in filtered if a["service_type"] == service_type.upper()]

        if search and search.strip():
            st = search.strip().lower()
            filtered = [
                a
                for a in filtered
                if st in a["application_id"].lower()
                or st in a["correlation_id"].lower()
                or st in a["citizen_reference_id"].lower()
                or st in a["citizen_name"].lower()
                or st in str(a.get("data_payload", {})).lower()
            ]

        reverse = sort_order.lower() == "desc"
        if clean_sort_by == "priority":
            priority_rank = {"URGENT": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}
            filtered.sort(key=lambda x: priority_rank.get(x.get("priority", "NORMAL"), 0), reverse=reverse)
        elif clean_sort_by == "status":
            filtered.sort(key=lambda x: x.get("status", ""), reverse=reverse)
        elif clean_sort_by == "application_id":
            filtered.sort(key=lambda x: x.get("application_id", ""), reverse=reverse)
        elif clean_sort_by == "citizen_name":
            filtered.sort(key=lambda x: str(x.get("citizen_name") or ""), reverse=reverse)
        elif clean_sort_by == "updated_at":
            filtered.sort(key=lambda x: x.get("updated_at") or datetime.min, reverse=reverse)
        else:
            filtered.sort(key=lambda x: x.get("received_at") or datetime.min, reverse=reverse)

        total = len(filtered)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        offset = (page - 1) * page_size
        paged_items = filtered[offset : offset + page_size]
        items = [self._to_summary_dict(a) for a in paged_items]
        return items, total, total_pages

    def get_dashboard_summary(self) -> Dict[str, Any]:
        apps = list(_MEM_APPLICATIONS.values())
        if self.db and not self._should_skip_db():
            try:
                db_apps = self.db.query(Application).all()
                if db_apps:
                    apps = [self._to_dict(a) for a in db_apps]
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed in get_dashboard_summary, using memory store: %s", exc)

        total_incoming = len(apps)
        pending = sum(1 for a in apps if a["status"] == "PENDING")
        processing = sum(1 for a in apps if a["status"] == "PROCESSING")
        completed = sum(1 for a in apps if a["status"] in ("VERIFIED", "COMPLETED"))
        rejected = sum(1 for a in apps if a["status"] == "REJECTED")
        action_required = sum(1 for a in apps if a["status"] == "ACTION_REQUIRED")
        failed_or_queued = sum(1 for a in apps if a["status"] in ("FAILED", "QUEUED"))

        now_date = datetime.now(timezone.utc).date()
        today_applications = 0
        for a in apps:
            r_at = a.get("received_at")
            if isinstance(r_at, datetime) and r_at.date() == now_date:
                today_applications += 1

        durations_minutes: List[float] = []
        for a in apps:
            if a["status"] in ("VERIFIED", "COMPLETED") and a.get("completed_at") and a.get("received_at"):
                rec = a["received_at"]
                comp = a["completed_at"]
                if isinstance(rec, datetime) and isinstance(comp, datetime):
                    diff_m = (comp - rec).total_seconds() / 60.0
                    if diff_m > 0:
                        durations_minutes.append(diff_m)

        if durations_minutes:
            avg_m = sum(durations_minutes) / len(durations_minutes)
            hours = int(avg_m // 60)
            mins = int(avg_m % 60)
            avg_time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        else:
            avg_time_str = "N/A"

        return {
            "total_incoming": total_incoming,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "rejected": rejected,
            "action_required": action_required,
            "failed_or_queued": failed_or_queued,
            "average_processing_time": avg_time_str,
            "today_applications": today_applications,
            "govmesh_connection": "DEMO ONLINE",
            "api_status": "ONLINE",
            "pending_events": failed_or_queued,
        }

    @staticmethod
    def _to_summary_dict(app: Dict[str, Any]) -> Dict[str, Any]:
        data = app.get("data_payload", {})
        new_addr = data.get("new_address", {})
        return {
            "id": app.get("id", ""),
            "application_id": app.get("application_id", ""),
            "correlation_id": app.get("correlation_id", ""),
            "citizen_reference_id": app.get("citizen_reference_id", ""),
            "citizen_name": app.get("citizen_name", ""),
            "service_type": app.get("service_type", "ADDRESS_CHANGE"),
            "requested_operation": app.get("requested_operation", "UPDATE_REVENUE_ADDRESS"),
            "priority": app.get("priority", "NORMAL"),
            "status": app.get("status", "PENDING"),
            "required_action": app.get("required_action", ""),
            "received_at": app.get("received_at"),
            "taluka": new_addr.get("taluka", "Haveli"),
            "district": new_addr.get("district", "Pune"),
        }

    @staticmethod
    def _to_dict(app: Application) -> Dict[str, Any]:
        payload = dict(app.data_payload or {})
        c_record = payload.get("consent_record")
        return {
            "id": app.id,
            "application_id": app.application_id,
            "correlation_id": app.correlation_id,
            "citizen_reference_id": app.citizen_reference_id,
            "service_type": app.service_type,
            "requested_operation": app.requested_operation,
            "purpose": app.purpose,
            "consent_reference": app.consent_reference,
            "priority": app.priority,
            "status": app.status,
            "required_action": app.required_action,
            "citizen_name": app.citizen_name,
            "received_at": app.received_at,
            "updated_at": app.updated_at,
            "processing_started_at": app.processing_started_at,
            "completed_at": app.completed_at,
            "assigned_officer_id": app.assigned_officer_id,
            "data_payload": payload,
            "workflow_history": app.workflow_history,
            "consent_record": c_record,
        }

    def get_document_by_id(self, document_id: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Locates a document across all applications. Returns (doc_dict, app_dict) if found.
        """
        clean_doc_id = document_id.strip()
        all_apps = self.get_all_applications()
        for app in all_apps:
            data_payload = app.get("data_payload", {})
            for doc in data_payload.get("proof_documents", []):
                if doc.get("document_id") == clean_doc_id:
                    return doc, app
        return None

    def attach_document(self, application_id: str, doc_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Attaches a new proof document to an application and persists to PostgreSQL if connected.
        """
        clean_id = application_id.strip()
        now = datetime.now(timezone.utc)
        if clean_id in _MEM_APPLICATIONS:
            rec = _MEM_APPLICATIONS[clean_id]
            data_payload = rec.setdefault("data_payload", {})
            proof_docs = data_payload.setdefault("proof_documents", [])
            # Avoid duplicate document ID attachment
            existing = [d for d in proof_docs if d.get("document_id") == doc_dict.get("document_id")]
            if not existing:
                proof_docs.append(doc_dict)
            rec["updated_at"] = now

        if self.db and not self._should_skip_db():
            try:
                db_app = self.db.query(Application).filter(Application.application_id == clean_id).first()
                if db_app:
                    payload = dict(db_app.data_payload or {})
                    proof_docs = list(payload.get("proof_documents", []))
                    json_safe_doc = {k: v for k, v in doc_dict.items() if not isinstance(v, bytes)}
                    existing = [d for d in proof_docs if d.get("document_id") == doc_dict.get("document_id")]
                    if not existing:
                        proof_docs.append(json_safe_doc)
                    payload["proof_documents"] = proof_docs
                    db_app.data_payload = payload
                    db_app.updated_at = now
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(db_app, "data_payload")
                    self.db.commit()
            except SQLAlchemyError as exc:
                self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB update failed in attach_document: %s", exc)

        return self.get_by_application_id(clean_id)

    def override_document(
        self, application_id: str, document_id: str, override_dict: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Records an officer manual override on a document and persists to PostgreSQL if connected.
        """
        clean_id = application_id.strip()
        clean_doc_id = document_id.strip()
        now = datetime.now(timezone.utc)
        if clean_id in _MEM_APPLICATIONS:
            rec = _MEM_APPLICATIONS[clean_id]
            data_payload = rec.setdefault("data_payload", {})
            for doc in data_payload.get("proof_documents", []):
                if doc.get("document_id") == clean_doc_id:
                    doc["verification_status"] = override_dict.get("decision", "VALIDATED")
                    doc["manual_override"] = override_dict
                    rec["updated_at"] = now

        if self.db and not self._should_skip_db():
            try:
                db_app = self.db.query(Application).filter(Application.application_id == clean_id).first()
                if db_app:
                    payload = dict(db_app.data_payload or {})
                    proof_docs = list(payload.get("proof_documents", []))
                    for doc in proof_docs:
                        if doc.get("document_id") == clean_doc_id:
                            doc["verification_status"] = override_dict.get("decision", "VALIDATED")
                            doc["manual_override"] = override_dict
                    payload["proof_documents"] = proof_docs
                    db_app.data_payload = payload
                    db_app.updated_at = now
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(db_app, "data_payload")
                    self.db.commit()
            except SQLAlchemyError as exc:
                self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB update failed in override_document: %s", exc)

        return self.get_by_application_id(clean_id)

    def save_application(self, app_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates an application record in memory and PostgreSQL."""
        clean_id = app_dict["application_id"]
        _MEM_APPLICATIONS[clean_id] = app_dict
        if self.db and not self._should_skip_db():
            try:
                db_app = self.db.query(Application).filter(Application.application_id == clean_id).first()
                if not db_app:
                    db_app = Application(
                        id=app_dict.get("id", f"APP-{clean_id}"),
                        application_id=clean_id,
                        correlation_id=app_dict.get("correlation_id", f"CORR-{clean_id}"),
                        citizen_reference_id=app_dict.get("citizen_reference_id", "CIT-GEN"),
                        service_type=app_dict.get("service_type", "ADDRESS_CHANGE"),
                        requested_operation=app_dict.get("requested_operation", "UPDATE_REVENUE_ADDRESS"),
                        purpose=app_dict.get("purpose", ""),
                        consent_reference=app_dict.get("consent_reference", ""),
                        priority=app_dict.get("priority", "NORMAL"),
                        status=app_dict.get("status", "PENDING"),
                        required_action=app_dict.get("required_action"),
                        citizen_name=app_dict.get("citizen_name", ""),
                        received_at=app_dict.get("received_at", datetime.now(timezone.utc)),
                        updated_at=app_dict.get("updated_at", datetime.now(timezone.utc)),
                        assigned_officer_id=app_dict.get("assigned_officer_id"),
                        data_payload=app_dict.get("data_payload", {}),
                        workflow_history=app_dict.get("workflow_history", []),
                    )
                    self.db.add(db_app)
                else:
                    db_app.data_payload = app_dict.get("data_payload", {})
                    db_app.status = app_dict.get("status", db_app.status)
                self.db.commit()
            except SQLAlchemyError as exc:
                self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB insert failed in save_application: %s", exc)
        return app_dict

    def create_new_application(self, app_dict: Dict[str, Any], auto_commit: bool = True) -> Dict[str, Any]:
        """
        Creates and persists a brand-new application record in memory and PostgreSQL.
        Guarantees idempotency checking and atomic insertion.
        """
        clean_id = app_dict["application_id"].strip()
        _MEM_APPLICATIONS[clean_id] = app_dict
        if self.db and not self._should_skip_db():
            try:
                db_app = Application(
                    id=app_dict.get("id", f"APP-{clean_id}"),
                    application_id=clean_id,
                    correlation_id=app_dict.get("correlation_id", f"CORR-{clean_id}"),
                    citizen_reference_id=app_dict.get("citizen_reference_id", "CIT-GEN"),
                    service_type=app_dict.get("service_type", "ADDRESS_CHANGE"),
                    requested_operation=app_dict.get("requested_operation", "UPDATE_REVENUE_ADDRESS"),
                    purpose=app_dict.get("purpose", "Update Revenue address record & 7/12 land registry linkage"),
                    consent_reference=app_dict.get("consent_reference", ""),
                    priority=app_dict.get("priority", "NORMAL"),
                    status=app_dict.get("status", "PENDING"),
                    required_action=app_dict.get("required_action", "Verify new residential address against Taluka land registry & electricity proof"),
                    citizen_name=app_dict.get("citizen_name", ""),
                    received_at=app_dict.get("received_at", datetime.now(timezone.utc)),
                    updated_at=app_dict.get("updated_at", datetime.now(timezone.utc)),
                    assigned_officer_id=app_dict.get("assigned_officer_id"),
                    data_payload=app_dict.get("data_payload", {}),
                    workflow_history=app_dict.get("workflow_history", []),
                )
                self.db.add(db_app)
                if auto_commit:
                    self.db.commit()
                else:
                    self.db.flush()
            except SQLAlchemyError as exc:
                if auto_commit:
                    self.db.rollback()
                self._mark_db_failed()
                logger.warning("DB insert failed in create_new_application: %s", exc)
                raise
        return self.get_by_application_id(clean_id) or app_dict



