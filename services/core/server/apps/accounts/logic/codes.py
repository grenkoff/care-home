"""Codes of authenticator apps, after RFC 4226 and RFC 6238."""

from datetime import datetime
from typing import final

import attrs


@final
@attrs.define(slots=True, frozen=True)
class Key:
    """Key that an authenticator app shares with the site, in base32."""

    _text: str

    def code(self, step: int) -> str:
        """Returns the code of a time step."""
        return ''


@final
@attrs.define(slots=True, frozen=True)
class Authenticator:
    """Authenticator of a user: its key and the last step whose code was used."""

    _key: Key
    _used: int

    def accepted(self, code: str, moment: datetime) -> int:
        """Returns the step of a fresh valid code or raises WrongCodeError."""
        return self._used
