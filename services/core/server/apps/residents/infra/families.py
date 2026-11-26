"""Families kept in the tables of residents."""

import uuid
from typing import final

import attrs

from server.apps.residents.logic.family import Member


@final
@attrs.define(slots=True, frozen=True)
class StoredFamilies:
    """Links of residents to relatives kept in the table of kinships."""

    def members(self, relative: uuid.UUID) -> tuple[Member, ...]:
        """Returns the residents in the home whom the relative follows."""
        return ()
