"""Tests of the admin where staff keep the residents of the home."""

import datetime as dt
from http import HTTPStatus
from types import MappingProxyType
from typing import Final

import pytest
from django.test import Client

from server.apps.residents.models import Resident

_ADD: Final = '/admin/residents/resident/add/'
_MARIA: Final = 'Maria Ivanova'
_ADMITTED: Final = MappingProxyType({
    'full_name': _MARIA,
    'moved_in_on': '2026-01-10',
})


@pytest.mark.django_db
def test_staff_add_a_resident(admin_client: Client) -> None:
    admin_client.post(_ADD, dict(_ADMITTED))

    assert list(
        Resident.objects.values_list('full_name', 'moved_in_on', 'moved_out_on'),
    ) == [(_MARIA, dt.date(2026, 1, 10), None)]


@pytest.mark.django_db
def test_staff_set_the_move_out(admin_client: Client) -> None:
    resident = Resident.objects.create(
        full_name=_MARIA,
        moved_in_on=dt.date(2026, 1, 10),
    )

    admin_client.post(
        f'/admin/residents/resident/{resident.pk}/change/',
        {**_ADMITTED, 'moved_out_on': '2026-03-01'},
    )

    resident.refresh_from_db()
    assert resident.moved_out_on == dt.date(2026, 3, 1)


@pytest.mark.django_db
def test_refuses_a_move_out_before_the_move_in(admin_client: Client) -> None:
    response = admin_client.post(
        _ADD,
        {**_ADMITTED, 'moved_out_on': '2026-01-09'},
    )

    assert response.status_code == HTTPStatus.OK
    assert not Resident.objects.exists()
