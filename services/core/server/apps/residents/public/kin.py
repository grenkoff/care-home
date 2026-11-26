"""Facade of residents that other modules ask about relatives."""

import uuid
from typing import Protocol


class Kin(Protocol):
    """Facade: relatives of the residents who live in the home."""

    def related(self, relative: uuid.UUID) -> bool:
        """Tells whether the account has a working link to a resident in the home."""
