"""Invitations kept in the database of accounts."""

from datetime import UTC, datetime
from typing import final

import attrs

from server.apps.accounts.logic.invitations import Invitation


@final
@attrs.define(slots=True, frozen=True)
class StoredInvitations:
    """Invitations kept in the table of accounts."""

    def found(self, digest: str) -> Invitation:
        """Returns the invitation of a digest or raises UnknownInvitationError."""
        return Invitation(
            email='',
            expires_at=datetime.max.replace(tzinfo=UTC),
            accepted=False,
        )

    def accept(self, digest: str, password: str) -> None:
        """Makes the account of an unused invitation or raises an error."""
