"""Tests of the page that shows the key of a new authenticator app."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

_PAGE: Final = '/en/second-factor/connect/'


@pytest.mark.django_db
@pytest.mark.parametrize('fragment', ['otpauth://totp/', 'data:image/svg+xml'])
def test_key_is_shown_as_a_link_and_a_picture(
    pending: Client,
    fragment: str,
) -> None:
    assert fragment in pending.get(_PAGE).content.decode()


@pytest.mark.django_db
def test_key_stays_until_the_app_is_connected(
    pending: Client,
    shown_key: str,
) -> None:
    assert f'secret={shown_key}' in pending.get(_PAGE).content.decode()


@pytest.mark.django_db
def test_connecting_needs_the_password_first(client: Client) -> None:
    response = client.get(_PAGE)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/sign-in/'
