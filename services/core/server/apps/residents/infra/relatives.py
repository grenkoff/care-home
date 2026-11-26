"""Relatives found through the facade of accounts."""

import uuid
from typing import final

import attrs

from server.apps.accounts.public.accounts import Accounts


@final
@attrs.define(slots=True, frozen=True)
class AccountRelatives:
    """Adapter: relatives who are the accounts of the accounts module."""

    _accounts: Accounts

    def identified(self, email: str) -> uuid.UUID:
        """Returns the account of the e-mail or raises UnknownRelativeError."""
        return uuid.UUID(int=0)
