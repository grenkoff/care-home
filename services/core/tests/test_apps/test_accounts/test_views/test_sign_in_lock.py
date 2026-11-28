"""Tests of the lock that wrong passwords put on signing in."""

from http import HTTPStatus
from typing import Final

import pytest
from django.conf import LazySettings
from django.test import Client

from server.apps.accounts.models import User

pytestmark = pytest.mark.django_db

_CHOSEN: Final = 'a long secret'
_OLGA: Final = 'olga@example.test'


@pytest.fixture(autouse=True)
def _locks(settings: LazySettings) -> None:
    """Turns the lock of wrong passwords on, as it is outside tests."""
    settings.AUTHENTICATION_BACKENDS = (
        'axes.backends.AxesBackend',
        *settings.AUTHENTICATION_BACKENDS,
    )
    User.objects.create_user(username=_OLGA, password=_CHOSEN)


def _locked(client: Client, language: str = 'en') -> str:
    """Tries wrong passwords for Olga until the lock and returns the page."""
    page = f'/{language}/sign-in/'
    for _ in range(3):
        client.post(page, {'username': _OLGA, 'password': 'a wrong guess'})
    response = client.post(page, {'username': _OLGA, 'password': _CHOSEN})
    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    return response.content.decode()


@pytest.mark.parametrize('fragment', ['<!DOCTYPE html>', 'Try again in 15 minutes.'])
def test_wrong_passwords_lock_for_a_while(
    client: Client,
    fragment: str,
) -> None:
    assert fragment in _locked(client)


def test_lock_speaks_russian(client: Client) -> None:
    assert 'Попробуйте снова через 15 минут.' in _locked(client, 'ru')
