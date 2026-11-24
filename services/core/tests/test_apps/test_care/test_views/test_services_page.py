"""Tests of the page that lists the care services and their prices."""

import pytest
from django.test import Client

from server.apps.care.models import Service


@pytest.fixture
def services() -> None:
    """Keeps two care services, the second one placed first by staff."""
    Service.objects.create(
        position=2,
        name_ru='Прогулки',
        name_en='Walks',
        description_ru='Под липами',
        description_en='In the garden',
        price_cents=300_000,
    )
    Service.objects.create(
        position=1,
        name_ru='Уход',
        name_en='Care',
        description_ru='Днём и ночью',
        description_en='Day and night',
        price_cents=4_500_000,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('services')
@pytest.mark.parametrize(
    ('language', 'expected'),
    [
        (
            'ru',
            ['Уход', 'Днём и ночью', '45000.00', 'Прогулки', 'Под липами', '3000.00'],
        ),
        ('en', ['Care', 'Day and night', '45000.00', 'Walks', 'In the garden']),
    ],
)
def test_services_follow_the_order_staff_set(
    client: Client,
    language: str,
    expected: list[str],
) -> None:
    page = client.get(f'/{language}/services/').content.decode()

    found = [page.find(text) for text in expected]

    assert -1 not in found
    assert found == sorted(found)
