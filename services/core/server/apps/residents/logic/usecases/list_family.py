"""Use case that lists the residents whom a relative follows."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import attrs

if TYPE_CHECKING:
    import uuid

    from server.apps.residents.logic.family import Families, Member


@final
@attrs.define(slots=True, frozen=True)
class ListFamily:
    """Lists the residents in the home whom a relative follows."""

    _families: Families

    def __call__(self, relative: uuid.UUID) -> tuple[Member, ...]:
        """Returns the residents of the links of the relative that work."""
        return self._families.members(relative)
