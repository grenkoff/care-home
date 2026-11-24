"""Care services kept in the database of care."""

from typing import final

import attrs

from server.apps.care import models
from server.apps.care.logic.services import Bilingual, Offer


@final
@attrs.define(slots=True, frozen=True)
class StoredOffers:
    """Care services kept in the table of care."""

    def listed(self) -> list[Offer]:
        """Reads every care service in the order staff set."""
        return [
            Offer(
                name=Bilingual(stored.name_ru, stored.name_en),
                description=Bilingual(stored.description_ru, stored.description_en),
                price_cents=stored.price_cents,
            )
            for stored in models.Service.objects.order_by('position')
        ]
