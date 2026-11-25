"""Use cases that open an invitation link and accept it."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import attrs

from server.apps.accounts.logic.invitations import Digest

if TYPE_CHECKING:
    from server.apps.accounts.logic.invitations import Clock, Invitations


@final
@attrs.define(slots=True, frozen=True)
class OpenInvitation:
    """Opens the link of an invitation that is neither used nor expired."""

    _invitations: Invitations
    _clock: Clock

    def __call__(self, token: str) -> str:
        """Returns the e-mail invited or raises UnknownInvitationError."""
        invitation = self._invitations.found(Digest(token).hexadecimal())
        return invitation.opened_at(self._clock.now())


@final
@attrs.define(slots=True, frozen=True)
class AcceptInvitation:
    """Makes the account of an open invitation with the password chosen."""

    _invitations: Invitations
    _clock: Clock

    def __call__(self, token: str, password: str) -> None:
        """Makes the account or raises UnknownInvitationError."""
        digest = Digest(token).hexadecimal()
        self._invitations.accept(digest, password, self._clock.now())
