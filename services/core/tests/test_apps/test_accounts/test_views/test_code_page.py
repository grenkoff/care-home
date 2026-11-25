"""Tests of the page that asks for the code of a connected authenticator app."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client
from django.utils import timezone

from server.apps.accounts.logic.codes import Key
from server.apps.accounts.logic.constants import CODE_SECONDS

_PAGE: Final = '/en/second-factor/'
_FIELD: Final = 'code'


def _code(key: str, shift: int = 0) -> str:
    """Gives the code of the key for the current step moved by a shift."""
    step = int(timezone.now().timestamp()) // CODE_SECONDS
    return Key(key).code(step + shift)


@pytest.mark.django_db
def test_page_asks_for_the_code_and_hides_the_key(
    pending: Client,
    connected_key: str,
) -> None:
    page = pending.get(_PAGE)

    assert page.status_code == HTTPStatus.OK
    assert 'name="code"' in page.content.decode()
    assert connected_key not in page.content.decode()


@pytest.mark.django_db
def test_valid_code_signs_in(pending: Client, connected_key: str) -> None:
    response = pending.post(_PAGE, {_FIELD: _code(connected_key)}, follow=True)

    assert response.redirect_chain == [('/en/', HTTPStatus.FOUND)]
    assert 'Sign out' in response.content.decode()


@pytest.mark.django_db
def test_wrong_code_does_not_sign_in(pending: Client, connected_key: str) -> None:
    response = pending.post(_PAGE, {_FIELD: _code(connected_key, 5)})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'This code is wrong or no longer valid.' in response.content.decode()
    assert 'Sign out' not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('connected_key')
@pytest.mark.parametrize('method', ['get', 'post'])
def test_connected_app_is_not_connected_again(pending: Client, method: str) -> None:
    response = getattr(pending, method)('/en/second-factor/connect/')

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == _PAGE


@pytest.mark.django_db
def test_code_needs_the_password_first(client: Client) -> None:
    response = client.get(_PAGE)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/sign-in/'
