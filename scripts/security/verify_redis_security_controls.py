#!/usr/bin/env python3
"""
Validate Redis availability and backend distributed security controls.

Usage:
  REDIS_URL=redis://localhost:6379/0 python scripts/security/verify_redis_security_controls.py
"""

from __future__ import annotations

import os
import sys
import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        print("[WARN] REDIS_URL is not set.")
        return 2

    try:
        redis = importlib.import_module("redis")
    except Exception as exc:
        print(f"[WARN] redis package is not available: {exc}")
        return 2

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        pong = client.ping()
        if not pong:
            print("[WARN] Redis ping did not return True.")
            return 2
        print("[OK] Redis ping successful.")
    except Exception as exc:
        print(f"[WARN] Redis connection failed: {exc}")
        return 2

    try:
        security_utils = importlib.import_module("app.core.security_utils")
    except Exception as exc:
        print(f"[WARN] Could not import app.core.security_utils: {exc}")
        return 2

    limiter_name = type(security_utils.login_rate_limiter).__name__
    blacklist_name = type(security_utils.token_blacklist).__name__

    print(f"Detected login rate limiter: {limiter_name}")
    print(f"Detected token blacklist: {blacklist_name}")

    ok = limiter_name == "RedisRateLimiter" and blacklist_name == "RedisTokenBlacklist"
    if ok:
        print("[OK] Distributed security controls are using Redis backends.")
        return 0

    print("[WARN] Security controls are not using Redis backends (fallback likely active).")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
