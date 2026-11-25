"""Tests of invitations that are refused."""

from http import HTTPStatus
from typing import Final

import pytest
from django.conf import LazySettings
from django.test import Client
from django.utils import timezone

from server.apps.accounts.models import Invitation, User

_CHOSEN: Final = 'a long secret of anna'
_GONE: Final = 'This link no longer works'


def _sent(first: str, second: str, consent: str = 'on') -> dict[str, str]:
    """Returns the form of an invitation as a relative fills it in."""
    return {'new_password1': first, 'new_password2': second, 'consent': consent}


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
@pytest.mark.parametrize(
    'sent',
    [
        _sent(_CHOSEN, _CHOSEN, consent=''),
        _sent(_CHOSEN, 'another'),
        _sent('short', 'short'),
    ],
)
def test_incomplete_acceptance_is_refused(
    client: Client,
    settings: LazySettings,
    invitation_page: str,
    sent: dict[str, str],
) -> None:
    settings.AUTH_PASSWORD_VALIDATORS = [
        {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    ]

    response = client.post(invitation_page, sent)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert not User.objects.exists()


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
def test_existing_account_is_not_invited_again(
    client: Client,
    invitation_page: str,
) -> None:
    User.objects.create_user(username='anna@example.test', password=_CHOSEN)

    response = client.post(
        invitation_page,
        _sent(_CHOSEN, _CHOSEN),
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'already has an account' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize('method', ['get', 'post'])
def test_expired_link_is_refused(
    client: Client,
    invitation: Invitation,
    invitation_page: str,
    method: str,
) -> None:
    Invitation.objects.filter(pk=invitation.pk).update(expires_at=timezone.now())

    response = getattr(client, method)(invitation_page)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert _GONE in response.content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
@pytest.mark.parametrize('method', ['get', 'post'])
def test_unknown_link_is_refused(client: Client, method: str) -> None:
    response = getattr(client, method)('/en/invitation/guess/')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert _GONE in response.content.decode()
