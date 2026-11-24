"""Use case that lists the care services of the home."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import attrs

from server.apps.care.logic.services import CareService

if TYPE_CHECKING:
    from server.apps.care.logic.services import Offers


@final
@attrs.define(slots=True, frozen=True)
class ListServices:
    """Lists the care services in the order staff set, in one language."""

    _offers: Offers

    def __call__(self, language: str) -> list[CareService]:
        """Returns the care services with their texts in the language."""
        return [
            CareService(
                name=offer.name.said_in(language),
                description=offer.description.said_in(language),
                price_cents=offer.price_cents,
            )
            for offer in self._offers.listed()
        ]
