"""Tests of the admin where staff keep the care services."""

import pytest
from django.test import Client

from server.apps.care.models import Service


@pytest.mark.django_db
@pytest.mark.parametrize(
    'column',
    ['Прогулки', 'Walks', '300000', '<td class="field-position">7</td>'],
)
def test_staff_see_both_names_price_and_position(
    admin_client: Client,
    column: str,
) -> None:
    Service.objects.create(
        position=7,
        name_ru='Прогулки',
        name_en='Walks',
        description_ru='Под липами',
        description_en='In the garden',
        price_cents=300_000,
    )

    response = admin_client.get('/admin/care/service/')

    assert column in response.content.decode()
