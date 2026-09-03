import time
import threading
from typing import Dict, List, Optional
from fastapi import Request
from app.core.errors import RateLimitExceededError
from app.core.logging import logger


class AuthRateLimiter:
    """
    Sliding window in-memory rate limiter for authentication endpoints.
    Protects sensitive endpoints (e.g. /auth/login, /auth/reauthenticate)
    against automated credential stuffing and brute-force attacks.
    
    Default: 5 requests per 60 seconds per client IP.
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def _clean_old_requests(self, ip: str, now: float) -> None:
        cutoff = now - self.window_seconds
        self._requests[ip] = [ts for ts in self._requests[ip] if ts > cutoff]

    def check(self, client_ip: str) -> None:
        """
        Validates whether the client IP has exceeded the request threshold.
        Raises RateLimitExceededError (HTTP 429) if exceeded, otherwise records the request.
        """
        now = time.time()
        with self._lock:
            if client_ip not in self._requests:
                self._requests[client_ip] = []

            self._clean_old_requests(client_ip, now)

            if len(self._requests[client_ip]) >= self.max_requests:
                oldest_timestamp = self._requests[client_ip][0]
                retry_after = max(1, int(oldest_timestamp + self.window_seconds - now))
                logger.warning(
                    "Authentication rate limit exceeded for IP '%s' (%d requests in %ds). Retry-After: %ds",
                    client_ip,
                    len(self._requests[client_ip]),
                    self.window_seconds,
                    retry_after,
                )
                raise RateLimitExceededError(
                    message=f"Too many authentication attempts. Please retry after {retry_after} seconds.",
                    retry_after=retry_after,
                )

            self._requests[client_ip].append(now)

    def reset(self) -> None:
        """Resets all tracked client IP request histories (used for test isolation)."""
        with self._lock:
            self._requests.clear()


# Singleton limiter instance for auth endpoints
auth_limiter = AuthRateLimiter(max_requests=5, window_seconds=60)


def extract_client_ip(request: Request) -> str:
    """
    Extracts client IP address securely.
    Avoids blindly trusting arbitrary spoofed X-Forwarded-For headers.
    Falls back to direct connection host.
    """
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def check_auth_rate_limit(request: Request) -> None:
    """
    FastAPI dependency to enforce rate limiting on authentication routes.
    """
    client_ip = extract_client_ip(request)
    auth_limiter.check(client_ip)


def reset_rate_limiter() -> None:
    """Helper to reset rate limiter in unit and integration test fixtures."""
    auth_limiter.reset()
