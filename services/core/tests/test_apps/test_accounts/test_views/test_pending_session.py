"""Tests of the session between the password and the code."""

from typing import Final

import pytest
from django.conf import LazySettings
from django.test import Client
from django.utils import timezone

from server.apps.accounts.logic.codes import Key
from server.apps.accounts.logic.constants import CODE_SECONDS
from server.apps.accounts.models import User

_CHOSEN: Final = 'a long secret'
_BORIS: Final = 'boris@example.test'
_SIGN_IN: Final = '/en/sign-in/'
_CONNECT: Final = '/en/second-factor/connect/'


@pytest.mark.django_db
def test_password_starts_a_new_session(client: Client) -> None:
    User.objects.create_user(username=_BORIS, password=_CHOSEN)
    session = client.session
    session.save()

    client.post(_SIGN_IN, {'username': _BORIS, 'password': _CHOSEN})

    assert client.session.session_key != session.session_key


@pytest.mark.django_db
def test_next_person_gets_a_fresh_key(pending: Client, shown_key: str) -> None:
    User.objects.create_user(username=_BORIS, password=_CHOSEN)

    pending.post(_SIGN_IN, {'username': _BORIS, 'password': _CHOSEN})

    assert shown_key not in pending.get(_CONNECT).content.decode()


@pytest.mark.django_db
def test_session_before_the_code_ends_soon(pending: Client) -> None:
    assert pending.session.get_expiry_age() == 10 * 60


@pytest.mark.django_db
def test_session_after_the_code_lasts_as_usual(
    pending: Client,
    connected_key: str,
    settings: LazySettings,
) -> None:
    step = int(timezone.now().timestamp()) // CODE_SECONDS

    pending.post('/en/second-factor/', {'code': Key(connected_key).code(step)})

    assert pending.session.get_expiry_age() == settings.SESSION_COOKIE_AGE


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('key', 'page'),
    [('shown_key', _CONNECT), ('connected_key', '/en/second-factor/')],
)
def test_pages_of_the_codes_are_never_cached(
    pending: Client,
    request: pytest.FixtureRequest,
    key: str,
    page: str,
) -> None:
    request.getfixturevalue(key)

    assert 'no-store' in pending.get(page).headers.get('Cache-Control', '')
