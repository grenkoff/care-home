"""Facade of accounts that other modules find by e-mail."""

import uuid
from typing import Protocol, final


@final
class UnknownAccountError(LookupError):
    """Raised for an e-mail that has no account."""

    __slots__ = ()


class Accounts(Protocol):
    """Facade: accounts of people who sign in, found by their e-mail."""

    def identified(self, email: str) -> uuid.UUID:
        """Returns the id of the account of the e-mail, regardless of case."""
