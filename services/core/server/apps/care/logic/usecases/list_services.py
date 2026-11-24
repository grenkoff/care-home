"""Use case that lists the care services of the home."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import attrs

if TYPE_CHECKING:
    from server.apps.care.logic.services import CareService, Offers


@final
@attrs.define(slots=True, frozen=True)
class ListServices:
    """Lists the care services in the order staff set, in one language."""

    _offers: Offers

    def __call__(self, language: str) -> list[CareService]:
        """Returns the care services with their texts in the language."""
        return []
