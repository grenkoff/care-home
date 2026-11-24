"""Clock and tokens of the system that the use cases of accounts read."""

import secrets
from datetime import datetime
from typing import Final, final

import attrs
from django.utils import timezone

_TOKEN_BYTES: Final = 32


@final
@attrs.define(slots=True, frozen=True)
class SystemClock:
    """Clock of the system."""

    def now(self) -> datetime:
        """Returns the current moment in UTC."""
        return timezone.now()


@final
@attrs.define(slots=True, frozen=True)
class SystemTokens:
    """Tokens from the random source of the operating system."""

    def fresh(self) -> str:
        """Returns a new token that is safe to put in a link."""
        return secrets.token_urlsafe(_TOKEN_BYTES)
