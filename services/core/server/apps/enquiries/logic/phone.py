"""Phone numbers that visitors leave to be called back."""

import re
import string
from typing import Final, final

import attrs

_SHAPE: Final = re.compile(r'\+?[0-9 ()-]+')
_FEWEST_DIGITS: Final = 7
_MOST_DIGITS: Final = 15


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
        number = self._text.strip()
        digits = sum(symbol in string.digits for symbol in number)
        if not _SHAPE.fullmatch(number):
            raise InvalidPhoneError(number)
        if not _FEWEST_DIGITS <= digits <= _MOST_DIGITS:
            raise InvalidPhoneError(number)
        return number
