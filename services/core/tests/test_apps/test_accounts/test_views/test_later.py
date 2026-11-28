"""Tests of putting off the authenticator app, which only staff may do."""

from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User

pytestmark = pytest.mark.django_db

_CHOSEN: Final = 'a long secret'
_LATER: Final = 'action="/en/second-factor/later/"'
_CONNECT: Final = '/en/second-factor/connect/'


@pytest.fixture
def staff(client: Client) -> Client:
    """Client of staff without an app who gave the password for the admin."""
    User.objects.create_user(username='olga', password=_CHOSEN, is_staff=True)
    client.post('/en/sign-in/?next=/admin/', {'username': 'olga', 'password': _CHOSEN})
    return client


def test_staff_may_connect_the_app_later(staff: Client) -> None:
    assert _LATER in staff.get(_CONNECT).content.decode()
