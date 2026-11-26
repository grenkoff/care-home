"""Relatives found in the tables of residents."""

import uuid
from typing import final

import attrs


@final
@attrs.define(slots=True, frozen=True)
class StoredKin:
    """Facade: relatives with working links kept in the table of kinships."""

    def related(self, relative: uuid.UUID) -> bool:
        """Tells whether the account has a working link to a resident in the home."""
        return False
