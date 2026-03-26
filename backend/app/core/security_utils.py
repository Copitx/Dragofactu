"""
Security utilities: Rate limiting, password validation, token blacklist.
"""
import os
import logging
import re
import time
from collections import defaultdict
from threading import Lock
from typing import Set, Dict, Tuple
from fastapi import HTTPException, status, Request

try:
    import redis
except ImportError:  # pragma: no cover - optional dependency at runtime
    redis = None


logger = logging.getLogger(__name__)


# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

class PasswordValidator:
    """Validate password complexity requirements."""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str) -> Tuple[bool, str]:
        """
        Validate password meets security requirements.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < cls.MIN_LENGTH:
            return False, f"La contraseña debe tener al menos {cls.MIN_LENGTH} caracteres"

        if len(password) > cls.MAX_LENGTH:
            return False, f"La contraseña no puede exceder {cls.MAX_LENGTH} caracteres"

        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una mayúscula"

        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una minúscula"

        if not re.search(r'\d', password):
            return False, "La contraseña debe contener al menos un número"

        # Check for common weak passwords
        weak_passwords = {
            'password', 'password123', '12345678', 'qwerty123',
            'admin123', 'letmein', 'welcome', 'monkey123'
        }
        if password.lower() in weak_passwords:
            return False, "Contraseña demasiado común, elige otra"

        return True, ""

    @classmethod
    def validate_or_raise(cls, password: str):
        """Validate password or raise HTTPException."""
        is_valid, error = cls.validate(password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )


# ============================================================================
# RATE LIMITING (In-Memory)
# ============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, use Redis-based solution.
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

    def _cleanup_old_requests(self, key: str, current_time: float):
        """Remove requests outside the time window."""
        cutoff = current_time - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        current_time = time.time()

        with self.lock:
            self._cleanup_old_requests(key, current_time)

            if len(self.requests[key]) >= self.max_requests:
                return False

            self.requests[key].append(current_time)
            return True

    def get_retry_after(self, key: str) -> int:
        """Get seconds until rate limit resets."""
        if not self.requests[key]:
            return 0

        oldest = min(self.requests[key])
        retry_after = int(self.window_seconds - (time.time() - oldest))
        return max(0, retry_after)


class RedisRateLimiter:
    """
    Redis-backed fixed-window rate limiter.
    Uses atomic INCR + EXPIRE to share limits across instances.
    """

    def __init__(self, redis_client, prefix: str, max_requests: int = 5, window_seconds: int = 60):
        self.redis = redis_client
        self.prefix = prefix
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def _key(self, key: str) -> str:
        return f"rl:{self.prefix}:{key}"

    def is_allowed(self, key: str) -> bool:
        redis_key = self._key(key)
        try:
            current = self.redis.incr(redis_key)
            if current == 1:
                self.redis.expire(redis_key, self.window_seconds)
            return current <= self.max_requests
        except Exception as e:
            logger.warning("Redis rate limiter error, allowing request: %s", e)
            return True

    def get_retry_after(self, key: str) -> int:
        redis_key = self._key(key)
        try:
            ttl = self.redis.ttl(redis_key)
            if ttl is None or ttl < 0:
                return 0
            return int(ttl)
        except Exception:
            return 0


def _build_redis_client():
    """Build redis client from REDIS_URL when available."""
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url or redis is None:
        return None
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info("Using Redis-backed security controls.")
        return client
    except Exception as e:
        logger.warning("Redis unavailable, using in-memory fallback: %s", e)
        return None


_redis_client = _build_redis_client()

if _redis_client:
    login_rate_limiter = RedisRateLimiter(_redis_client, prefix="login", max_requests=5, window_seconds=300)
    register_rate_limiter = RedisRateLimiter(_redis_client, prefix="register", max_requests=3, window_seconds=3600)
    api_rate_limiter = RedisRateLimiter(_redis_client, prefix="api", max_requests=120, window_seconds=60)
else:
    # Global rate limiters (fallback)
    login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 attempts per 5 min
    register_rate_limiter = RateLimiter(max_requests=3, window_seconds=3600)  # 3 per hour
    # Global API rate limiter: 120 requests/minute per IP
    api_rate_limiter = RateLimiter(max_requests=120, window_seconds=60)


def check_login_rate_limit(request: Request):
    """Check rate limit for login endpoint."""
    client_ip = request.client.host if request.client else "unknown"

    if not login_rate_limiter.is_allowed(client_ip):
        retry_after = login_rate_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos de login. Intenta de nuevo en {retry_after} segundos",
            headers={"Retry-After": str(retry_after)}
        )


def check_register_rate_limit(request: Request):
    """Check rate limit for register endpoint."""
    client_ip = request.client.host if request.client else "unknown"

    if not register_rate_limiter.is_allowed(client_ip):
        retry_after = register_rate_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados registros desde esta IP. Intenta de nuevo más tarde",
            headers={"Retry-After": str(retry_after)}
        )


# ============================================================================
# TOKEN BLACKLIST (In-Memory)
# ============================================================================

class TokenBlacklist:
    """
    Simple in-memory token blacklist.
    For production, use Redis with TTL.
    """

    def __init__(self):
        self.blacklisted: Set[str] = set()
        self.lock = Lock()
        # Track when tokens were added to cleanup old ones
        self.token_times: Dict[str, float] = {}

    def add(self, token: str, ttl_seconds: int = 86400):
        """Add token to blacklist."""
        with self.lock:
            self.blacklisted.add(token)
            self.token_times[token] = time.time() + ttl_seconds

    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        self._cleanup()
        return token in self.blacklisted

    def _cleanup(self):
        """Remove expired blacklist entries."""
        current_time = time.time()
        with self.lock:
            expired = [t for t, exp in self.token_times.items() if exp < current_time]
            for token in expired:
                self.blacklisted.discard(token)
                del self.token_times[token]


class RedisTokenBlacklist:
    """Redis-backed token blacklist with per-token TTL."""

    def __init__(self, redis_client, prefix: str = "token_blacklist"):
        self.redis = redis_client
        self.prefix = prefix

    def _key(self, token: str) -> str:
        return f"{self.prefix}:{token}"

    def add(self, token: str, ttl_seconds: int = 86400):
        try:
            self.redis.setex(self._key(token), ttl_seconds, "1")
        except Exception as e:
            logger.warning("Redis blacklist add failed: %s", e)

    def is_blacklisted(self, token: str) -> bool:
        try:
            return self.redis.exists(self._key(token)) == 1
        except Exception as e:
            logger.warning("Redis blacklist check failed: %s", e)
            return False


if _redis_client:
    token_blacklist = RedisTokenBlacklist(_redis_client)
else:
    token_blacklist = TokenBlacklist()


# ============================================================================
# INPUT SANITIZATION
# ============================================================================

def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Basic string sanitization.
    SQLAlchemy handles SQL injection, but this adds extra safety.
    """
    if not value:
        return value

    # Truncate to max length
    value = value[:max_length]

    # Remove null bytes
    value = value.replace('\x00', '')

    # Strip whitespace
    value = value.strip()

    return value


def sanitize_username(username: str) -> str:
    """Sanitize username - alphanumeric and underscore only."""
    username = sanitize_string(username, 50)
    # Remove any non-alphanumeric characters except underscore
    username = re.sub(r'[^\w]', '', username)
    return username.lower()
