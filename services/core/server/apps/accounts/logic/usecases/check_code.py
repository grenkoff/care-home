"""Use case that checks the code of a connected authenticator app."""

import uuid
from typing import final

import attrs

from server.apps.accounts.logic.authenticators import Codes
from server.apps.accounts.logic.invitations import Clock


@final
@attrs.define(slots=True, frozen=True)
class CheckCode:
    """Checks the code that the authenticator app of a user shows."""

    _codes: Codes
    _clock: Clock

    def __call__(self, user: uuid.UUID, code: str) -> None:
        """Uses a fresh valid code or raises WrongCodeError."""
        self._codes.use(user, code, self._clock.now())
