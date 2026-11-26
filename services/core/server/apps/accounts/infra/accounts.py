"""Accounts kept in the table of users."""

import uuid
from typing import final

import attrs

from server.apps.accounts import models
from server.apps.accounts.public.accounts import UnknownAccountError


@final
@attrs.define(slots=True, frozen=True)
class StoredAccounts:
    """Facade: accounts found in the table of users by their e-mail."""

    def identified(self, email: str) -> uuid.UUID:
        """Returns the id of the account of the e-mail, regardless of case."""
        found = (
            models.User.objects
            .filter(username__iexact=email)
            .values_list('pk', flat=True)
            .first()
        )
        if found is None:
            raise UnknownAccountError
        return found
