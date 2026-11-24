"""Tests of the admin where staff read the enquiries of visitors."""

from datetime import UTC, datetime
from typing import Final

import pytest
from django.test import Client

from server.apps.enquiries.models import Enquiry

_LIST: Final = '/admin/enquiries/enquiry/'
_PHONE: Final = '+7 495 123-45-67'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'column',
    ['Anna', _PHONE, 'field-sent_at', 'field-handled'],
)
def test_staff_see_whom_to_call(admin_client: Client, column: str) -> None:
    Enquiry.objects.create(name='Anna', phone=_PHONE)

    page = admin_client.get(_LIST).content.decode()

    assert column in page


@pytest.mark.django_db
def test_staff_see_the_newest_enquiry_first(admin_client: Client) -> None:
    Enquiry.objects.create(
        name='Older',
        phone=_PHONE,
        sent_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    Enquiry.objects.create(
        name='Newer',
        phone=_PHONE,
        sent_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    page = admin_client.get(_LIST).content.decode()

    assert page.index('Newer') < page.index('Older')


@pytest.mark.django_db
def test_staff_mark_chosen_enquiries_handled(admin_client: Client) -> None:
    chosen = Enquiry.objects.create(name='Chosen', phone=_PHONE)
    Enquiry.objects.create(name='Other', phone=_PHONE)

    admin_client.post(
        _LIST,
        {'action': 'mark_handled', '_selected_action': [str(chosen.pk)]},
    )

    assert list(
        Enquiry.objects.order_by('name').values_list('name', 'handled'),
    ) == [('Chosen', True), ('Other', False)]
