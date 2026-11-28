"""Tests of the names that staff and relatives sign in with."""

from typing import Final

import pytest
from django.conf import LazySettings
from django.test import Client

from server.apps.accounts.models import User

pytestmark = pytest.mark.django_db

_CHOSEN: Final = 'a long secret'
_OLGA: Final = 'olga'
_NEXT: Final = '/en/second-factor/'


def _signed_in(client: Client, name: str) -> bool:
    """Tells whether the password under the name leads to the second factor."""
    response = client.post(
        '/en/sign-in/',
        {'username': name, 'password': _CHOSEN},
    )
    return response.get('Location') == _NEXT


@pytest.mark.parametrize('name', [_OLGA, 'Olga@Example.TEST'])
def test_staff_sign_in_with_a_name_or_an_email(client: Client, name: str) -> None:
    User.objects.create_user(
        username=_OLGA,
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


def test_shared_staff_emails_sign_in_no_one(client: Client) -> None:
    for name in (_OLGA, 'oleg'):
        User.objects.create_user(
            username=name,
            email='desk@example.test',
            password=_CHOSEN,
            is_staff=True,
        )

    assert not _signed_in(client, 'desk@example.test')


def test_apps_of_staff_are_named_by_user_name(
    client: Client,
    settings: LazySettings,
) -> None:
    settings.SITE_NAME = 'Quiet Garden'
    User.objects.create_user(username=_OLGA, password=_CHOSEN, is_staff=True)
    _signed_in(client, _OLGA)

    page = client.get('/en/second-factor/connect/').content.decode()

    assert 'otpauth://totp/Quiet%20Garden%3Aolga?' in page
