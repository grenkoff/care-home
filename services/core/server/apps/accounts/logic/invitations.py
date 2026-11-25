"""Invitations through which relatives get their accounts."""

import hashlib
from datetime import datetime
from typing import Protocol, final

import attrs

from server.apps.accounts.logic.errors import UnknownInvitationError


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Invitation:
    """Invitation as the site keeps it: for whom, until when, whether used."""

    _email: str
    _expires_at: datetime
    _accepted: bool

    def opened_at(self, moment: datetime) -> str:
        """Returns the e-mail while the link works or raises UnknownInvitationError."""
        if self._accepted or moment >= self._expires_at:
            raise UnknownInvitationError
        return self._email


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


class Invitations(Protocol):
    """Invitations that staff made."""

    def found(self, digest: str) -> Invitation:
        """Returns the invitation of a digest or raises UnknownInvitationError."""

    def accept(self, digest: str, password: str, moment: datetime) -> None:
        """Makes the account of an unused invitation or raises an error."""
