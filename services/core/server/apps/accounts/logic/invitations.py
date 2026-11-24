"""Invitations through which relatives get their accounts."""

from datetime import datetime
from typing import Protocol, final

import attrs


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
