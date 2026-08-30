from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.core.permissions import get_permissions_for_role
from app.core.errors import (
    AuthenticationError,
    InactiveAccountError,
    ResourceNotFoundError,
    ReauthenticationRequiredError,
)
from app.core.logging import logger


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate(self, identifier: str, password: str) -> Tuple[Dict[str, Any], str, int]:
        """
        Authenticates a user via Username / Email / Mobile and Password.
        Returns: (user_dict, access_token, expires_in_seconds)
        """
        user = self.user_repo.get_by_identifier(identifier)
        if not user:
            logger.warning("Authentication failed: unknown identifier '%s'", identifier)
            raise AuthenticationError(message="Invalid credentials. Please verify your identifier and password.")

        if not user.get("is_active", False):
            logger.warning("Authentication rejected: user '%s' is inactive", user["username"])
            raise InactiveAccountError(message="This department account has been deactivated. Please contact your Department Administrator.")

        if not verify_password(password, user["password_hash"]):
            logger.warning("Authentication failed: invalid password for user '%s'", user["username"])
            raise AuthenticationError(message="Invalid credentials. Please verify your identifier and password.")

        # Update last login timestamp
        self.user_repo.update_last_login(user["id"])

        # Generate JWT access token
        token_payload = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
        token = create_access_token(token_payload)
        expires_in = 30 * 60  # 30 minutes in seconds

        logger.info("Authentication successful: user '%s' logged in with role '%s'", user["username"], user["role"])
        return user, token, expires_in

    def reauthenticate(self, user_id: str, password: str) -> bool:
        """
        Verifies credentials for sensitive actions.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(message="User not found.")

        if not verify_password(password, user["password_hash"]):
            logger.warning("Re-authentication failed for user '%s'", user["username"])
            raise AuthenticationError(message="Invalid credentials. Re-authentication failed.", code="REAUTHENTICATION_FAILED")

        logger.info("Re-authentication confirmed for user '%s'", user["username"])
        return True

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Returns the full profile for an authenticated user."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(message="User profile not found.")
        return user
