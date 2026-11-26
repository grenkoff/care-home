"""People who may watch the cameras of the home."""

import uuid
from typing import Protocol


class Viewers(Protocol):
    """Accounts that may watch the cameras."""

    def admitted(self, viewer: uuid.UUID) -> bool:
        """Tells whether the account may watch the cameras now."""
