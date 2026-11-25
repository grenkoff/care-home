"""Authenticator apps that users connect as the second factor."""

import uuid
from datetime import datetime
from typing import Protocol


class Authenticators(Protocol):
    """Authenticator apps that users connected."""

    def connected(self, user: uuid.UUID) -> bool:
        """Tells whether the user connected an authenticator app."""

    def connect(self, user: uuid.UUID, key: str, step: int) -> None:
        """Keeps the key of the user and the step of its first code."""


class Keys(Protocol):
    """Source of keys nobody can guess."""

    def fresh(self) -> str:
        """Returns a new key in base32."""


class Codes(Protocol):
    """Codes of the authenticator apps that users connected."""

    def use(self, user: uuid.UUID, code: str, moment: datetime) -> None:
        """Uses a fresh valid code of the app of the user or raises WrongCodeError."""
