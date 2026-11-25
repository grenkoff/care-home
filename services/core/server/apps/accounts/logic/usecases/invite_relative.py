"""Use case that invites a relative to get an account."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import attrs

from server.apps.accounts.logic.invitations import Digest, Issued

if TYPE_CHECKING:
    from datetime import timedelta

    from server.apps.accounts.logic.clock import Clock
    from server.apps.accounts.logic.invitations import Tokens


@final
@attrs.define(slots=True, frozen=True)
class InviteRelative:
    """Makes a one-time invitation that expires after its lifetime."""

    _tokens: Tokens
    _clock: Clock
    _lifetime: timedelta

    def __call__(self) -> Issued:
        """Returns the code to send and what the site keeps of it."""
        code = self._tokens.fresh()
        return Issued(
            code=code,
            digest=Digest(code).hexadecimal(),
            expires_at=self._clock.now() + self._lifetime,
        )
