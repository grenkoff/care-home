"""Codes of authenticator apps, after RFC 4226 and RFC 6238."""

import base64
import hmac
from datetime import datetime
from typing import Final, final

import attrs

from server.apps.accounts.logic.constants import CODE_DIGITS, CODE_DRIFT, CODE_SECONDS
from server.apps.accounts.logic.errors import WrongCodeError

_COUNTER_BYTES: Final = 8
_NUMBER_BYTES: Final = 4
_OFFSET_MASK: Final = 0xF
_NUMBER_MASK: Final = 0x7FFFFFFF


@final
@attrs.define(slots=True, frozen=True)
class Key:
    """Key that an authenticator app shares with the site, in base32."""

    _text: str

    def code(self, step: int) -> str:
        """Returns the code of a time step."""
        digest = hmac.digest(
            base64.b32decode(self._text),
            step.to_bytes(_COUNTER_BYTES),
            'sha1',
        )
        offset = digest[-1] & _OFFSET_MASK
        number = int.from_bytes(digest[offset : offset + _NUMBER_BYTES])
        return str((number & _NUMBER_MASK) % 10**CODE_DIGITS).zfill(CODE_DIGITS)


@final
@attrs.define(slots=True, frozen=True)
class Totp:
    """Time-based codes of a key that were not used before a step."""

    _key: Key
    _used: int

    def accepted(self, code: str, moment: datetime) -> int:
        """Returns the step of a fresh valid code or raises WrongCodeError."""
        now = int(moment.timestamp()) // CODE_SECONDS
        steps = [
            step
            for step in range(now - CODE_DRIFT, now + CODE_DRIFT + 1)
            if step > self._used and hmac.compare_digest(self._key.code(step), code)
        ]
        if not steps:
            raise WrongCodeError
        return steps[0]
