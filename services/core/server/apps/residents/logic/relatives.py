"""Relatives of residents, known by the id of their account."""

import uuid
from typing import Protocol


class Relatives(Protocol):
    """Relatives who have an account to sign in with."""

    def identified(self, email: str) -> uuid.UUID:
        """Returns the account of the e-mail or raises UnknownRelativeError."""
