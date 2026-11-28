"""Tests of the names that staff and relatives sign in with."""

from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User

pytestmark = pytest.mark.django_db

_CHOSEN: Final = 'a long secret'
_NEXT: Final = '/en/second-factor/'


def _signed_in(client: Client, name: str) -> bool:
    """Tells whether the password under the name leads to the second factor."""
    response = client.post(
        '/en/sign-in/',
        {'username': name, 'password': _CHOSEN},
    )
    return response.get('Location') == _NEXT


@pytest.mark.parametrize('name', ['olga', 'Olga@Example.TEST'])
def test_staff_sign_in_with_a_name_or_an_email(client: Client, name: str) -> None:
    User.objects.create_user(
        username='olga',
        email='olga@example.test',
        password=_CHOSEN,
        is_staff=True,
    )

    assert _signed_in(client, name)


@pytest.mark.parametrize('name', ['boris', 'boris@example.test'])
def test_relatives_sign_in_only_by_an_email_name(
    client: Client,
    name: str,
) -> None:
    User.objects.create_user(
        username='boris',
        email='boris@example.test',
        password=_CHOSEN,
    )

    assert not _signed_in(client, name)
