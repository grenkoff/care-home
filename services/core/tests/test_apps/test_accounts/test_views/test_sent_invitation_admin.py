"""Tests of the invitations that staff already sent."""

from http import HTTPStatus

import pytest
from django.test import Client

from server.apps.accounts.models import Invitation


@pytest.mark.django_db
def test_sent_invitation_cannot_be_changed(
    admin_client: Client,
    invitation: Invitation,
) -> None:
    digest = invitation.digest

    response = admin_client.post(
        f'/admin/accounts/invitation/{invitation.pk}/change/',
        {'email': 'boris@example.test'},
    )

    invitation.refresh_from_db()
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert (invitation.email, invitation.digest) == ('anna@example.test', digest)


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
@pytest.mark.parametrize('column', ['field-expires_at', 'field-accepted_at'])
def test_staff_see_whether_a_link_still_works(
    admin_client: Client,
    column: str,
) -> None:
    page = admin_client.get('/admin/accounts/invitation/').content.decode()

    assert column in page
