"""Limits of the accounts of relatives."""

from datetime import UTC, datetime, timedelta
from typing import Final

DIGEST_LENGTH: Final = 64
KEY_BYTES: Final = 20
KEY_LENGTH: Final = KEY_BYTES * 8 // 5
CODE_DIGITS: Final = 6
CODE_SECONDS: Final = 30
CODE_DRIFT: Final = 1
CODE_ATTEMPTS: Final = 5
CODE_LOCK_MINUTES: Final = 15
CODE_LOCK: Final = timedelta(minutes=CODE_LOCK_MINUTES)
UNLOCKED: Final = datetime.fromtimestamp(0, tz=UTC)
