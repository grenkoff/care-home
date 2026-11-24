"""Invitations through which relatives get their accounts."""

import hashlib
from datetime import datetime
from typing import Protocol, final

import attrs


@final
@attrs.define(slots=True, frozen=True)
class Digest:
    """Digest of a token: what the site keeps instead of the token."""

    _token: str

    def hexadecimal(self) -> str:
        """Returns the SHA-256 of the token in hexadecimal."""
        return hashlib.sha256(self._token.encode()).hexdigest()


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Issued:
    """Invitation just made: its one-time code, the digest kept and the expiry."""

    code: str
    digest: str
    expires_at: datetime


class Clock(Protocol):
    """Source of the current moment."""

    def now(self) -> datetime:
        """Returns the current moment with its time zone."""


class Tokens(Protocol):
    """Source of tokens nobody can guess."""

    def fresh(self) -> str:
        """Returns a new token for a link."""
