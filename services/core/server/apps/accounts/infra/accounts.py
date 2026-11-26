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
        try:
            return models.User.objects.values_list('pk', flat=True).get(
                username__iexact=email,
            )
        except models.User.DoesNotExist as error:
            raise UnknownAccountError from error
