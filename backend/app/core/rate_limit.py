"""slowapi limiter — shared instance + helpers for per-user keys."""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _key_func(request: Request) -> str:
    """Prefer the authenticated user id; fall back to client IP."""
    user = getattr(request.state, "user", None)
    if user is not None and getattr(user, "id", None) is not None:
        return f"user:{user.id}"
    return get_remote_address(request)


limiter: Limiter = Limiter(key_func=_key_func, headers_enabled=True)
