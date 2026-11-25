"""Tests of signing in to the admin with both factors."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client
from django.utils import timezone

from server.apps.accounts.logic.codes import Key
from server.apps.accounts.logic.constants import CODE_SECONDS
from server.apps.accounts.models import Authenticator, User

_KEY: Final = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
_ADMIN: Final = '/admin/'
_CHOSEN: Final = 'a long secret'


@pytest.fixture
def staff(client: Client) -> Client:
    """Client of a staff member with an app who gave the password for the admin."""
    email = 'olga@example.test'
    user = User.objects.create_user(
        username=email,
        email=email,
        password=_CHOSEN,
        is_staff=True,
        is_superuser=True,
    )
    Authenticator.objects.create(user=user, key=_KEY, used_step=0)
    client.post(
        f'/en/sign-in/?next={_ADMIN}',
        {'username': email, 'password': _CHOSEN},
    )
    return client


def test_admin_login_leads_to_the_sign_in(client: Client) -> None:
    response = client.get(f'/admin/login/?next={_ADMIN}')

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == f'/ru/sign-in/?next={_ADMIN}'


@pytest.mark.django_db
def test_password_alone_does_not_open_the_admin(staff: Client) -> None:
    assert staff.get(_ADMIN).status_code == HTTPStatus.FOUND


@pytest.mark.django_db
def test_staff_reach_the_admin_after_the_code(staff: Client) -> None:
    step = int(timezone.now().timestamp()) // CODE_SECONDS

    response = staff.post(
        '/en/second-factor/',
        {'code': Key(_KEY).code(step)},
        follow=True,
    )

    assert response.redirect_chain == [(_ADMIN, HTTPStatus.FOUND)]
    assert response.status_code == HTTPStatus.OK
