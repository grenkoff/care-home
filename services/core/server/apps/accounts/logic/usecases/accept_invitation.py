"""Use cases that open an invitation link and accept it."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import attrs

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
        return ''


@final
@attrs.define(slots=True, frozen=True)
class AcceptInvitation:
    """Makes the account of an open invitation with the password chosen."""

    _opened: OpenInvitation
    _invitations: Invitations

    def __call__(self, token: str, password: str) -> None:
        """Makes the account or raises UnknownInvitationError."""
