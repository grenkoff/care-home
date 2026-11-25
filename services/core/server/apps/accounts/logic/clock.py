"""Clock that the use cases of accounts read."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Source of the current moment."""

    def now(self) -> datetime:
        """Returns the current moment with its time zone."""
