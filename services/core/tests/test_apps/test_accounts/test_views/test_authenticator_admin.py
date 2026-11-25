"""Tests of the admin where staff reset the second factor of a user."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import Authenticator

_PAGES: Final = '/admin/accounts/authenticator/'


@pytest.mark.django_db
def test_staff_reset_the_second_factor(
    admin_client: Client,
    pending: Client,
    connected_key: str,
) -> None:
    authenticator = Authenticator.objects.get(key=connected_key)

    admin_client.post(f'{_PAGES}{authenticator.pk}/delete/', {'post': 'yes'})

    response = pending.get('/en/second-factor/')
    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/second-factor/connect/'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'page',
    [
        _PAGES,
        '/admin/accounts/authenticator/{authenticator.pk}/change/',
        '/admin/accounts/user/{authenticator.user_id}/change/',
    ],
)
def test_admin_never_shows_the_key(
    admin_client: Client,
    connected_key: str,
    page: str,
) -> None:
    authenticator = Authenticator.objects.get(key=connected_key)

    response = admin_client.get(page.format(authenticator=authenticator))

    assert response.status_code == HTTPStatus.OK
    assert connected_key not in response.content.decode()


@pytest.mark.django_db
def test_staff_cannot_add_an_authenticator(admin_client: Client) -> None:
    assert admin_client.get(f'{_PAGES}add/').status_code == HTTPStatus.FORBIDDEN
