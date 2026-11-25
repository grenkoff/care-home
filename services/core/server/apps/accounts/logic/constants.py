"""Limits of the accounts of relatives."""

from typing import Final

DIGEST_LENGTH: Final = 64
KEY_BYTES: Final = 20
KEY_LENGTH: Final = KEY_BYTES * 8 // 5
CODE_DIGITS: Final = 6
CODE_SECONDS: Final = 30
CODE_DRIFT: Final = 1
