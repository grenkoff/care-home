"""Residents whom a relative follows."""

import uuid
from typing import Protocol, final

import attrs


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Member:
    """Resident as the relative sees them: the name and the kinship."""

    full_name: str
    kind: str


class Families(Protocol):
    """Links between residents and their relatives."""

    def members(self, relative: uuid.UUID) -> tuple[Member, ...]:
        """Returns the residents in the home whom the relative follows."""
