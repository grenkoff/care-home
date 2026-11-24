"""Tests of changing the password of a relative."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User

_PAGE: Final = '/en/password/'
_OLD: Final = 'a long secret of anna'
_NEW: Final = 'a new long secret of anna'


@pytest.fixture
def relative() -> User:
    """Relative with an account."""
    return User.objects.create_user(username='anna@example.test', password=_OLD)


@pytest.mark.django_db
def test_relative_changes_the_password(client: Client, relative: User) -> None:
    client.force_login(relative)

    response = client.post(
        _PAGE,
        {'old_password': _OLD, 'new_password1': _NEW, 'new_password2': _NEW},
    )

    relative.refresh_from_db()
    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/password/done/'
    assert relative.check_password(_NEW)


@pytest.mark.django_db
def test_changed_password_is_confirmed(client: Client, relative: User) -> None:
    client.force_login(relative)

    page = client.get('/en/password/done/').content.decode()

    assert 'Your password has been changed' in page


@pytest.mark.django_db
def test_header_offers_the_password_page(client: Client, relative: User) -> None:
    client.force_login(relative)

    assert f'href="{_PAGE}"' in client.get('/en/').content.decode()


def test_guest_is_sent_to_sign_in(client: Client) -> None:
    response = client.get(_PAGE)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/sign-in/?next=/en/password/'
