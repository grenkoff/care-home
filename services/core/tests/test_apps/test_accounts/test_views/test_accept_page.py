"""Tests of the page where a relative accepts an invitation."""

from http import HTTPStatus
from types import MappingProxyType
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import Invitation, User

_CHOSEN: Final = 'a long secret of anna'
_ACCEPTED = MappingProxyType({
    'new_password1': _CHOSEN,
    'new_password2': _CHOSEN,
    'consent': 'on',
})


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
@pytest.mark.parametrize(
    'fragment',
    [
        'anna@example.test',
        'name="new_password1"',
        'name="new_password2"',
        'name="consent"',
        'never record',
    ],
)
def test_invitation_asks_for_password_and_rules(
    client: Client,
    invitation_page: str,
    fragment: str,
) -> None:
    assert fragment in client.get(invitation_page).content.decode()


@pytest.mark.django_db
def test_accepted_invitation_makes_the_account(
    client: Client,
    invitation: Invitation,
    invitation_page: str,
) -> None:
    client.post(invitation_page, _ACCEPTED)

    assert [
        user.check_password(_CHOSEN)
        for user in User.objects.filter(username=invitation.email)
    ] == [True]


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
def test_accepted_invitation_leads_to_sign_in(
    client: Client,
    invitation_page: str,
) -> None:
    response = client.post(invitation_page, _ACCEPTED)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/sign-in/'


@pytest.mark.django_db
def test_accepted_invitation_is_closed(
    client: Client,
    invitation: Invitation,
    invitation_page: str,
) -> None:
    client.post(invitation_page, _ACCEPTED)

    invitation.refresh_from_db()
    assert invitation.accepted_at is not None
    assert client.get(invitation_page).status_code == HTTPStatus.NOT_FOUND
