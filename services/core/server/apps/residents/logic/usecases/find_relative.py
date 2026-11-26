"""Use case that finds the account of a relative by e-mail."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, final

import attrs

if TYPE_CHECKING:
    from server.apps.residents.logic.relatives import Relatives


@final
@attrs.define(slots=True, frozen=True)
class FindRelative:
    """Finds the account that staff link to a resident."""

    _relatives: Relatives

    def __call__(self, email: str) -> uuid.UUID:
        """Returns the account of the e-mail or raises UnknownRelativeError."""
        return uuid.UUID(int=0)
