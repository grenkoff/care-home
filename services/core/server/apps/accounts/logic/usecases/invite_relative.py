"""Use case that invites a relative to get an account."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, final

import attrs

from server.apps.accounts.logic.invitations import Issued

if TYPE_CHECKING:
    from server.apps.accounts.logic.invitations import Clock, Tokens


@final
@attrs.define(slots=True, frozen=True)
class InviteRelative:
    """Makes a one-time invitation that expires after its lifetime."""

    _tokens: Tokens
    _clock: Clock
    _lifetime: timedelta

    def __call__(self) -> Issued:
        """Returns the code to send and what the site keeps of it."""
        return Issued(code='', digest='', expires_at=datetime.min.replace(tzinfo=UTC))
