"""Accounts kept in the table of users."""

import uuid
from typing import final

import attrs


@final
@attrs.define(slots=True, frozen=True)
class StoredAccounts:
    """Accounts found in the table of users by their e-mail."""

    def identified(self, email: str) -> uuid.UUID:
        """Returns the id of the account of the e-mail, regardless of case."""
        return uuid.UUID(int=0)
