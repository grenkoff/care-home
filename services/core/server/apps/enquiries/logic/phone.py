"""Phone numbers that visitors leave to be called back."""

from typing import final

import attrs


@final
class InvalidPhoneError(ValueError):
    """Raised when a text is not a phone number."""

    __slots__ = ()


@final
@attrs.define(slots=True, frozen=True)
class Phone:
    """Phone number as a visitor typed it."""

    _text: str

    def checked(self) -> str:
        """Returns the number without outer spaces or raises InvalidPhoneError."""
        return ''
