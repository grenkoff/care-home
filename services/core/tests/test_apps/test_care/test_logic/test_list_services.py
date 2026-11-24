"""Tests of the use case that lists the care services of the home."""

from typing import final

import attrs
import pytest

from server.apps.care.logic.services import Bilingual, CareService, Offer
from server.apps.care.logic.usecases.list_services import ListServices

_OFFERS = (
    Offer(
        name=Bilingual('Уход', 'Care'),
        description=Bilingual('Днём и ночью', 'Day and night'),
        price_cents=4_500_000,
    ),
    Offer(
        name=Bilingual('Прогулки', 'Walks'),
        description=Bilingual('Под липами', 'In the garden'),
        price_cents=300_000,
    ),
)


@final
@attrs.define(slots=True, frozen=True)
class _Kept:
    """Fake: two care services in the order staff set."""

    def listed(self) -> list[Offer]:
        """Returns the care services."""
        return list(_OFFERS)


@pytest.mark.parametrize(
    ('language', 'expected'),
    [
        (
            'ru',
            [
                CareService('Уход', 'Днём и ночью', 4_500_000),
                CareService('Прогулки', 'Под липами', 300_000),
            ],
        ),
        (
            'en',
            [
                CareService('Care', 'Day and night', 4_500_000),
                CareService('Walks', 'In the garden', 300_000),
            ],
        ),
    ],
)
def test_services_speak_the_language(
    language: str,
    expected: list[CareService],
) -> None:
    assert ListServices(_Kept())(language) == expected
