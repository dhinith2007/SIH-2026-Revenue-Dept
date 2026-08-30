from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.db.seed import get_seeded_users_with_hashes
from app.core.logging import logger

# In-memory synchronized fallback store for offline/standalone execution
_MEM_USERS: Dict[str, Dict[str, Any]] = {}
_LAST_DB_CHECK_FAILED: float = 0.0
_DB_RETRY_INTERVAL_SECONDS: float = 30.0


def _init_memory_store():
    global _MEM_USERS
    if not _MEM_USERS:
        seeded = get_seeded_users_with_hashes()
        for u in seeded:
            _MEM_USERS[u["id"]] = {
                **u,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "last_login_at": None,
                "failed_login_attempts": 0,
                "locked_until": None,
            }


_init_memory_store()


class UserRepository:
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

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Finds user by unique ID."""
        if self.db and not self._should_skip_db():
            try:
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    return self._to_dict(user)
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed, using memory store fallback: %s", exc)

        return _MEM_USERS.get(user_id)

    def get_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Finds user by Username, Mobile, OR Email.
        Matches case-insensitively for email/username and exact for mobile.
        """
        clean_ident = identifier.strip().lower()
        if self.db and not self._should_skip_db():
            try:
                user = self.db.query(User).filter(
                    (User.username.ilike(clean_ident))
                    | (User.email.ilike(clean_ident))
                    | (User.mobile == identifier.strip())
                ).first()
                if user:
                    return self._to_dict(user)
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed, using memory store fallback: %s", exc)

        for u in _MEM_USERS.values():
            if (
                u["username"].lower() == clean_ident
                or u["email"].lower() == clean_ident
                or u["mobile"] == identifier.strip()
            ):
                return u
        return None

    def update_last_login(self, user_id: str) -> None:
        """Updates last_login_at timestamp and resets failed attempts."""
        now = datetime.now(timezone.utc)
        if self.db and not self._should_skip_db():
            try:
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    user.last_login_at = now
                    user.failed_login_attempts = 0
                    self.db.commit()
                    return
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB commit failed for last_login update: %s", exc)

        if user_id in _MEM_USERS:
            _MEM_USERS[user_id]["last_login_at"] = now
            _MEM_USERS[user_id]["failed_login_attempts"] = 0

    def list_all(self) -> List[Dict[str, Any]]:
        """Lists all department users."""
        if self.db and not self._should_skip_db():
            try:
                users = self.db.query(User).all()
                if users:
                    return [self._to_dict(u) for u in users]
            except SQLAlchemyError as exc:
                self._mark_db_failed()
                logger.warning("DB query failed, using memory store fallback: %s", exc)

        return list(_MEM_USERS.values())

    @staticmethod
    def _to_dict(user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "mobile": user.mobile,
            "password_hash": user.password_hash,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
            "division": user.division,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login_at": user.last_login_at,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until,
        }
