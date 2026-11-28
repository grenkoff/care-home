"""Tests of putting off the authenticator app, which only staff may do."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User

pytestmark = pytest.mark.django_db

_CHOSEN: Final = 'a long secret'
_LATER_PAGE: Final = '/en/second-factor/later/'
_LATER: Final = f'action="{_LATER_PAGE}"'
_CONNECT: Final = '/en/second-factor/connect/'


@pytest.fixture
def staff(client: Client) -> Client:
    """Client of staff without an app who gave the password for the admin."""
    User.objects.create_user(username='olga', password=_CHOSEN, is_staff=True)
    client.post('/en/sign-in/?next=/admin/', {'username': 'olga', 'password': _CHOSEN})
    return client


def test_staff_may_connect_the_app_later(staff: Client) -> None:
    assert _LATER in staff.get(_CONNECT).content.decode()


def test_later_signs_staff_in_where_they_go(staff: Client) -> None:
    response = staff.post(_LATER_PAGE)

    assert (response.get('Location'), staff.get('/admin/').status_code) == (
        '/admin/',
        HTTPStatus.OK,
    )


def test_relatives_are_not_offered_later(pending: Client) -> None:
    assert _LATER not in pending.get(_CONNECT).content.decode()


def test_later_signs_no_relative_in(pending: Client) -> None:
    response = pending.post(_LATER_PAGE)

    assert (response.status_code, pending.get(_CONNECT).status_code) == (
        HTTPStatus.FORBIDDEN,
        HTTPStatus.OK,
    )
