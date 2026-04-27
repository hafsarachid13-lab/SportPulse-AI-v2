from __future__ import annotations
from datetime import UTC, datetime
from threading import Lock

from backend.core.security import decode_access_token


class TokenBlacklistService:
    _lock = Lock()
    _revoked_tokens: dict[str, int] = {}

    @classmethod
    def revoke(cls, token: str) -> None:
        payload = decode_access_token(token)
        exp = int(payload.get("exp", 0)) if payload else int(datetime.now(UTC).timestamp())
        with cls._lock:
            cls._cleanup_locked()
            cls._revoked_tokens[token] = exp

    @classmethod
    def is_revoked(cls, token: str) -> bool:
        now_ts = int(datetime.now(UTC).timestamp())
        with cls._lock:
            cls._cleanup_locked(now_ts)
            return token in cls._revoked_tokens

    @classmethod
    def _cleanup_locked(cls, now_ts: int | None = None) -> None:
        now = now_ts if now_ts is not None else int(datetime.now(UTC).timestamp())
        expired = [token for token, exp in cls._revoked_tokens.items() if exp <= now]
        for token in expired:
            del cls._revoked_tokens[token]
